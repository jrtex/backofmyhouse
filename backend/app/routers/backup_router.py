import json
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import Response
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_admin
from app.models.user import User
from app.schemas.backup_schemas import (
    BackupExport,
    ConflictStrategy,
    ImportResult,
)
from app.services.backup_service import BackupService

router = APIRouter()


@router.get("/export")
async def export_recipes(
    recipe_ids: Optional[List[UUID]] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> Response:
    """
    Export recipes as JSON file download.
    Requires admin access.

    Args:
        recipe_ids: Optional list of recipe IDs to export. If not provided, exports all recipes.
    """
    backup = BackupService.export_recipes(db, recipe_ids=recipe_ids)

    json_content = backup.model_dump_json(indent=2)

    filename = f"recipes-backup-{datetime.utcnow().strftime('%Y-%m-%d')}.json"

    return Response(
        content=json_content,
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@router.post("/import", response_model=ImportResult)
async def import_recipes(
    file: UploadFile = File(...),
    conflict_strategy: ConflictStrategy = Query(default=ConflictStrategy.skip),
    selected_titles: Optional[List[str]] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> ImportResult:
    """
    Import recipes from JSON backup file.
    Requires admin access.

    Args:
        file: JSON backup file to import
        conflict_strategy: How to handle title conflicts (skip, replace, rename)
        selected_titles: Optional list of recipe titles to import. If not provided, imports all.

    Conflict strategies:
    - skip: Skip recipes that already exist (by title)
    - replace: Replace existing recipes with imported data
    - rename: Create new recipes with numbered suffix (e.g., "Title (2)")
    """
    if not file.filename or not file.filename.endswith(".json"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a JSON file",
        )

    try:
        content = await file.read()
        data = json.loads(content)
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid JSON: {str(e)}",
        )

    try:
        backup_data = BackupExport.model_validate(data)
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid backup format: {str(e)}",
        )

    result = BackupService.import_recipes(
        db=db,
        backup_data=backup_data,
        importing_user_id=current_user.id,
        conflict_strategy=conflict_strategy,
        selected_titles=selected_titles,
    )

    return result
