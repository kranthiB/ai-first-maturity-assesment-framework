#!/usr/bin/env node

/**
 * Build Script for JavaScript Assets
 * Concatenates and minifies JavaScript modules for production
 */

const fs = require('fs');
const path = require('path');

class JSBuilder {
    constructor() {
        this.srcDir = path.join(__dirname, 'src', 'js');
        this.distDir = path.join(__dirname, 'dist', 'js');
        this.modules = [
            'modules/utils.js',
            'modules/charts.js', 
            'modules/assessment.js',
            'main.js'
        ];
    }

    async build() {
        try {
            console.log('🚀 Starting JavaScript build process...');
            
            // Ensure dist directory exists
            this.ensureDistDirectory();
            
            // Concatenate modules
            const concatenated = await this.concatenateModules();
            
            // Write concatenated file
            const concatenatedPath = path.join(this.distDir, 'app.js');
            fs.writeFileSync(concatenatedPath, concatenated);
            console.log(`✅ Concatenated: ${concatenatedPath}`);
            
            // Create minified version (basic minification)
            const minified = this.minify(concatenated);
            const minifiedPath = path.join(this.distDir, 'app.min.js');
            fs.writeFileSync(minifiedPath, minified);
            console.log(`✅ Minified: ${minifiedPath}`);
            
            // Copy individual modules to dist
            await this.copyModules();
            
            // Generate source map info
            this.generateSourceMapInfo();
            
            console.log('🎉 Build completed successfully!');
            this.printBuildStats(concatenated, minified);
            
        } catch (error) {
            console.error('❌ Build failed:', error);
            process.exit(1);
        }
    }

    ensureDistDirectory() {
        const dirs = [
            this.distDir,
            path.join(this.distDir, 'modules')
        ];
        
        dirs.forEach(dir => {
            if (!fs.existsSync(dir)) {
                fs.mkdirSync(dir, { recursive: true });
                console.log(`📁 Created directory: ${dir}`);
            }
        });
    }

    async concatenateModules() {
        const banner = this.generateBanner();
        let concatenated = banner + '\n\n';
        
        for (const module of this.modules) {
            const modulePath = path.join(this.srcDir, module);
            
            if (fs.existsSync(modulePath)) {
                const content = fs.readFileSync(modulePath, 'utf8');
                concatenated += `\n/* === ${module} === */\n`;
                concatenated += content;
                concatenated += '\n';
                console.log(`📦 Added module: ${module}`);
            } else {
                console.warn(`⚠️  Module not found: ${module}`);
            }
        }
        
        return concatenated;
    }

    async copyModules() {
        for (const module of this.modules) {
            const srcPath = path.join(this.srcDir, module);
            const distPath = path.join(this.distDir, module);
            
            if (fs.existsSync(srcPath)) {
                // Ensure directory exists
                const distDir = path.dirname(distPath);
                if (!fs.existsSync(distDir)) {
                    fs.mkdirSync(distDir, { recursive: true });
                }
                
                // Copy file
                fs.copyFileSync(srcPath, distPath);
                console.log(`📋 Copied: ${module}`);
            }
        }
    }

    minify(code) {
        // Basic minification - remove comments, extra whitespace, and console.logs
        return code
            // Remove single-line comments (but preserve URLs)
            .replace(/\/\/(?![^\r\n]*:\/\/)[^\r\n]*/g, '')
            // Remove multi-line comments
            .replace(/\/\*[\s\S]*?\*\//g, '')
            // Remove console.log statements (except in error handlers)
            .replace(/console\.log\([^)]*\);?/g, '')
            // Remove extra whitespace
            .replace(/\s+/g, ' ')
            // Remove whitespace around operators and punctuation
            .replace(/\s*([{}();,:])\s*/g, '$1')
            // Remove leading/trailing whitespace
            .trim();
    }

    generateBanner() {
        const now = new Date();
        return `/*!
 * AI-First Software Engineering Maturity Assessment Framework
 * Core JavaScript Application Bundle
 * 
 * Built: ${now.toISOString()}
 * Version: 1.0.0
 * 
 * Modules included:
         * - Utils: Common utilities and helpers
         * - Charts: Chart.js integration and management (for results visualization)
         * - Assessment: Assessment form functionality
         * - Main: Application initialization and coordination
 * 
 * Copyright (c) ${now.getFullYear()}
 */`;
    }

    generateSourceMapInfo() {
        const sourceMap = {
            version: 3,
            sources: this.modules,
            names: [],
            mappings: '',
            file: 'app.min.js'
        };
        
        const sourceMapPath = path.join(this.distDir, 'app.min.js.map');
        fs.writeFileSync(sourceMapPath, JSON.stringify(sourceMap, null, 2));
        console.log(`🗺️  Source map: ${sourceMapPath}`);
    }

    printBuildStats(original, minified) {
        const originalSize = Buffer.byteLength(original, 'utf8');
        const minifiedSize = Buffer.byteLength(minified, 'utf8');
        const reduction = ((originalSize - minifiedSize) / originalSize * 100).toFixed(1);
        
        console.log('\n📊 Build Statistics:');
        console.log(`   Original size:  ${this.formatBytes(originalSize)}`);
        console.log(`   Minified size:  ${this.formatBytes(minifiedSize)}`);
        console.log(`   Size reduction: ${reduction}%`);
        console.log(`   Modules built:  ${this.modules.length}`);
    }

    formatBytes(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
}

// Run build if this script is executed directly
if (require.main === module) {
    const builder = new JSBuilder();
    builder.build();
}

module.exports = JSBuilder;
