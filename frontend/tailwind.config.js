/** @type {import('tailwindcss').Config} */
export default {
	content: ['./src/**/*.{html,js,svelte,ts}'],
	theme: {
		extend: {
			colors: {
				primary: {
					50: '#F0FDF4',
					100: '#DCFCE7',
					200: '#BBF7D0',
					300: '#86EFAC',
					400: '#4ADE80',
					500: '#22C55E',
					600: '#2D6A4F',
					700: '#245C43',
					800: '#1B4332',
					900: '#14312A'
				}
			}
		}
	},
	plugins: []
};
