<div align="center">
<img width="1200" height="475" alt="GHBanner" src="https://github.com/user-attachments/assets/0aa67016-6eaf-458a-adb2-6e31a0763ed6" />
</div>

# Run and deploy your AI Studio app

This contains everything you need to run your app locally.

View your app in AI Studio: https://ai.studio/apps/drive/1r29LSMqub4B9Y_EbA2t6JGsMQHvEhvAl

## Run Locally

**Prerequisites:**  Node.js


1. Install dependencies:
   `npm install`
2. Set the `GEMINI_API_KEY` in [.env.local](.env.local) to your Gemini API key
3. Run the app:
   `npm run dev`

## Development

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm test` - Run tests in watch mode
- `npm test -- --run` - Run tests once

### Continuous Integration

This project uses GitHub Actions for CI. The workflow automatically runs on:
- Push to `main` branch
- Pull requests to `main` branch

The CI pipeline includes:
- TypeScript type checking
- Running all tests
- Building the project

Tests are run on Node.js 18.x and 20.x to ensure compatibility.
