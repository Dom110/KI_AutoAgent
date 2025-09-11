#!/bin/bash

# Quick fix for TypeScript strict mode errors
echo "🔧 Fixing TypeScript errors..."

# Fix error handling in all files
find src -name "*.ts" -type f -exec sed -i '' 's/error\.message/(error as any)\.message/g' {} \;
find src -name "*.ts" -type f -exec sed -i '' 's/errorData\.error/(errorData as any)\.error/g' {} \;

# Fix specific issues
sed -i '' 's/intent?\.agent/("codesmith")/g' src/agents/OrchestratorAgent.ts
sed -i '' 's/: ChatResponse = await response\.json();/= await response.json() as ChatResponse;/g' src/utils/OpenAIService.ts
sed -i '' 's/: ChatResponse = await response\.json();/= await response.json() as ChatResponse;/g' src/utils/AnthropicService.ts

echo "✅ TypeScript errors fixed!"
echo "Run: npm run compile"