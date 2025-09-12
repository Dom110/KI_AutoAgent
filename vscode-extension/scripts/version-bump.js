#!/usr/bin/env node
/**
 * Automatic Version Increment Script for KI AutoAgent
 * Automatically increments version number based on change type
 */

const fs = require('fs');
const path = require('path');

// Version increment types
const VERSION_TYPES = {
    PATCH: 'patch',     // Bug fixes, small improvements
    MINOR: 'minor',     // New features, agent updates
    MAJOR: 'major'      // Breaking changes, major refactoring
};

/**
 * Parse current version from package.json
 * @returns {Object} Current version parts
 */
function getCurrentVersion() {
    const packagePath = path.join(__dirname, '..', 'package.json');
    const packageJson = JSON.parse(fs.readFileSync(packagePath, 'utf8'));
    const version = packageJson.version;
    const [major, minor, patch] = version.split('.').map(Number);
    
    return { major, minor, patch, current: version };
}

/**
 * Increment version based on type
 * @param {string} type - patch, minor, or major
 * @returns {string} New version string
 */
function incrementVersion(type) {
    const { major, minor, patch } = getCurrentVersion();
    
    switch (type) {
        case VERSION_TYPES.PATCH:
            return `${major}.${minor}.${patch + 1}`;
        case VERSION_TYPES.MINOR:
            return `${major}.${minor + 1}.0`;
        case VERSION_TYPES.MAJOR:
            return `${major + 1}.0.0`;
        default:
            throw new Error(`Invalid version type: ${type}. Use patch, minor, or major.`);
    }
}

/**
 * Update version in package.json
 * @param {string} newVersion - New version string
 * @param {string} changeDescription - Description of changes
 */
function updatePackageVersion(newVersion, changeDescription) {
    const packagePath = path.join(__dirname, '..', 'package.json');
    const packageJson = JSON.parse(fs.readFileSync(packagePath, 'utf8'));
    
    // Update version
    packageJson.version = newVersion;
    
    // Add version history if it doesn't exist
    if (!packageJson.versionHistory) {
        packageJson.versionHistory = {};
    }
    
    // Add current version to history
    packageJson.versionHistory[newVersion] = {
        date: new Date().toISOString(),
        description: changeDescription,
        timestamp: Date.now()
    };
    
    // Write back to package.json
    fs.writeFileSync(packagePath, JSON.stringify(packageJson, null, 2) + '\n');
    
    console.log(`📦 Updated package.json version: ${newVersion}`);
    return packageJson;
}

/**
 * Update CLAUDE.md with new version info
 * @param {string} newVersion - New version string
 * @param {string} changeDescription - Description of changes
 */
function updateClaudeMd(newVersion, changeDescription) {
    const claudeMdPath = path.join(__dirname, '..', '..', 'CLAUDE.md');
    
    if (fs.existsSync(claudeMdPath)) {
        let content = fs.readFileSync(claudeMdPath, 'utf8');
        
        // Find the version history section and update it
        const versionHistoryRegex = /```markdown\n📦 Version History:\n(├──[^\n]+\n)*/g;
        const dateStr = new Date().toLocaleDateString('de-DE');
        const newVersionLine = `├── v${newVersion} (${dateStr}) - ${changeDescription}`;
        
        if (content.match(versionHistoryRegex)) {
            // Replace existing version history
            content = content.replace(
                versionHistoryRegex,
                `\`\`\`markdown\n📦 Version History:\n${newVersionLine}\n`
            );
        } else {
            // Add version history section if it doesn't exist
            const versionSection = `
## 📦 Version History

\`\`\`markdown
📦 Version History:
${newVersionLine}
\`\`\`
`;
            content = versionSection + content;
        }
        
        fs.writeFileSync(claudeMdPath, content);
        console.log(`📝 Updated CLAUDE.md with version ${newVersion}`);
    }
}

/**
 * Main version bump function
 */
function bumpVersion() {
    const args = process.argv.slice(2);
    
    if (args.length < 1) {
        console.error('❌ Error: Version type is required');
        console.log('Usage: npm run version:bump <type> [description]');
        console.log('Types: patch, minor, major');
        console.log('Examples:');
        console.log('  npm run version:bump patch "Fix OpusArbitrator output display"');
        console.log('  npm run version:bump minor "Add new agent features"');
        console.log('  npm run version:bump major "Breaking API changes"');
        process.exit(1);
    }
    
    const versionType = args[0].toLowerCase();
    const changeDescription = args[1] || 'Version bump';
    
    if (!Object.values(VERSION_TYPES).includes(versionType)) {
        console.error(`❌ Error: Invalid version type "${versionType}"`);
        console.log('Valid types: patch, minor, major');
        process.exit(1);
    }
    
    try {
        const currentVersion = getCurrentVersion();
        const newVersion = incrementVersion(versionType);
        
        console.log(`🔄 Bumping version from ${currentVersion.current} to ${newVersion}`);
        console.log(`📋 Change: ${changeDescription}`);
        console.log(`🏷️  Type: ${versionType.toUpperCase()}`);
        
        // Update package.json
        updatePackageVersion(newVersion, changeDescription);
        
        // Update CLAUDE.md
        updateClaudeMd(newVersion, changeDescription);
        
        console.log('');
        console.log('✅ Version bump completed successfully!');
        console.log('');
        console.log('Next steps:');
        console.log('1. Review the changes');
        console.log('2. Compile the extension: npm run compile');
        console.log('3. Test the extension in VS Code');
        console.log('4. Commit the changes: git add . && git commit -m "v' + newVersion + ': ' + changeDescription + '"');
        
    } catch (error) {
        console.error('❌ Error during version bump:', error.message);
        process.exit(1);
    }
}

// Auto-detect change type based on git changes (optional)
function detectChangeType() {
    // This could analyze git diff to suggest version type
    // For now, we'll keep it simple and require manual specification
    return null;
}

// Run the script
if (require.main === module) {
    bumpVersion();
}

module.exports = {
    getCurrentVersion,
    incrementVersion,
    updatePackageVersion,
    VERSION_TYPES
};