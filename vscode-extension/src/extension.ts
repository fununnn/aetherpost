import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

export function activate(context: vscode.ExtensionContext) {
    console.log('AutoPromo extension is now active!');

    // Check if AutoPromo is configured
    updateConfigurationContext();

    // Register commands
    registerCommands(context);
    
    // Register providers
    registerProviders(context);

    // Watch for configuration changes
    const watcher = vscode.workspace.createFileSystemWatcher('**/campaign.yaml');
    watcher.onDidCreate(() => updateConfigurationContext());
    watcher.onDidChange(() => updateConfigurationContext());
    watcher.onDidDelete(() => updateConfigurationContext());

    context.subscriptions.push(watcher);
}

function registerCommands(context: vscode.ExtensionContext) {
    // Initialize AutoPromo
    const initCommand = vscode.commands.registerCommand('autopromo.init', async () => {
        try {
            const terminal = getTerminal();
            
            // Check if project files exist for auto-detection
            const hasProjectFiles = await checkProjectFiles();
            
            if (hasProjectFiles) {
                const choice = await vscode.window.showQuickPick([
                    'Auto-detect from project',
                    'Quick setup',
                    'Interactive wizard'
                ], {
                    placeHolder: 'How would you like to initialize AutoPromo?'
                });

                switch (choice) {
                    case 'Auto-detect from project':
                        terminal.sendText('autopromo init auto');
                        break;
                    case 'Quick setup':
                        terminal.sendText('autopromo init --quick');
                        break;
                    case 'Interactive wizard':
                        terminal.sendText('autopromo wizard');
                        break;
                }
            } else {
                terminal.sendText('autopromo quickstart');
            }
            
            terminal.show();
        } catch (error) {
            vscode.window.showErrorMessage(`AutoPromo initialization failed: ${error}`);
        }
    });

    // Quick Start Guide
    const quickStartCommand = vscode.commands.registerCommand('autopromo.quickStart', async () => {
        const panel = vscode.window.createWebviewPanel(
            'autoPromoQuickStart',
            'AutoPromo Quick Start',
            vscode.ViewColumn.One,
            {
                enableScripts: true
            }
        );

        panel.webview.html = getQuickStartWebviewContent();
    });

    // Plan Campaign
    const planCommand = vscode.commands.registerCommand('autopromo.plan', async () => {
        try {
            const result = await execAsync('autopromo plan --format json');
            
            if (result.stdout) {
                const previewData = JSON.parse(result.stdout);
                showPreviewPanel(previewData);
            } else {
                vscode.window.showWarningMessage('No preview data available');
            }
        } catch (error) {
            vscode.window.showErrorMessage(`Failed to generate preview: ${error}`);
        }
    });

    // Execute Campaign
    const applyCommand = vscode.commands.registerCommand('autopromo.apply', async () => {
        const config = vscode.workspace.getConfiguration('autopromo');
        const confirmBeforePosting = config.get('confirmBeforePosting', true);

        if (confirmBeforePosting) {
            const choice = await vscode.window.showWarningMessage(
                'This will post to your configured social media platforms. Continue?',
                'Yes, Post Now',
                'Cancel'
            );

            if (choice !== 'Yes, Post Now') {
                return;
            }
        }

        const terminal = getTerminal();
        terminal.sendText('autopromo apply');
        terminal.show();

        vscode.window.showInformationMessage('Campaign execution started. Check terminal for progress.');
    });

    // Quick Post
    const quickPostCommand = vscode.commands.registerCommand('autopromo.quickPost', async () => {
        const message = await vscode.window.showInputBox({
            placeHolder: 'Enter your message to post',
            prompt: 'Quick post to social media'
        });

        if (!message) {
            return;
        }

        const platforms = await vscode.window.showQuickPick([
            'twitter',
            'twitter,bluesky',
            'twitter,bluesky,linkedin',
            'custom'
        ], {
            placeHolder: 'Select platforms'
        });

        if (!platforms) {
            return;
        }

        let platformArg = platforms;
        if (platforms === 'custom') {
            const customPlatforms = await vscode.window.showInputBox({
                placeHolder: 'Enter platforms (comma-separated)',
                prompt: 'e.g., twitter,bluesky,mastodon'
            });
            if (!customPlatforms) {
                return;
            }
            platformArg = customPlatforms;
        }

        const terminal = getTerminal();
        terminal.sendText(`autopromo now "${message}" --to ${platformArg}`);
        terminal.show();
    });

    // View Analytics
    const statsCommand = vscode.commands.registerCommand('autopromo.stats', async () => {
        try {
            const result = await execAsync('autopromo stats --format json');
            
            if (result.stdout) {
                const statsData = JSON.parse(result.stdout);
                showAnalyticsPanel(statsData);
            } else {
                const terminal = getTerminal();
                terminal.sendText('autopromo stats');
                terminal.show();
            }
        } catch (error) {
            vscode.window.showErrorMessage(`Failed to load analytics: ${error}`);
        }
    });

    // Open Configuration
    const openConfigCommand = vscode.commands.registerCommand('autopromo.openConfig', async () => {
        const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
        if (!workspaceFolder) {
            vscode.window.showErrorMessage('No workspace folder found');
            return;
        }

        const configPath = path.join(workspaceFolder.uri.fsPath, 'campaign.yaml');
        
        if (fs.existsSync(configPath)) {
            const doc = await vscode.workspace.openTextDocument(configPath);
            await vscode.window.showTextDocument(doc);
        } else {
            const choice = await vscode.window.showInformationMessage(
                'No campaign.yaml found. Would you like to create one?',
                'Yes',
                'No'
            );
            
            if (choice === 'Yes') {
                vscode.commands.executeCommand('autopromo.init');
            }
        }
    });

    // Validate Configuration
    const validateConfigCommand = vscode.commands.registerCommand('autopromo.validateConfig', async () => {
        try {
            const result = await execAsync('autopromo validate');
            
            if (result.stderr) {
                vscode.window.showErrorMessage(`Configuration errors: ${result.stderr}`);
            } else {
                vscode.window.showInformationMessage('Configuration is valid!');
            }
        } catch (error) {
            vscode.window.showErrorMessage(`Validation failed: ${error}`);
        }
    });

    // Setup Credentials
    const setupCredentialsCommand = vscode.commands.registerCommand('autopromo.setupCredentials', async () => {
        const terminal = getTerminal();
        terminal.sendText('autopromo setup wizard');
        terminal.show();
    });

    // Register all commands
    context.subscriptions.push(
        initCommand,
        quickStartCommand,
        planCommand,
        applyCommand,
        quickPostCommand,
        statsCommand,
        openConfigCommand,
        validateConfigCommand,
        setupCredentialsCommand
    );
}

function registerProviders(context: vscode.ExtensionContext) {
    // Campaign Status Provider
    const campaignProvider = new CampaignStatusProvider();
    vscode.window.registerTreeDataProvider('autopromo.campaign', campaignProvider);

    // Quick Actions Provider
    const quickActionsProvider = new QuickActionsProvider();
    vscode.window.registerTreeDataProvider('autopromo.quickActions', quickActionsProvider);

    // Analytics Provider (if data exists)
    const analyticsProvider = new AnalyticsProvider();
    vscode.window.registerTreeDataProvider('autopromo.analytics', analyticsProvider);

    context.subscriptions.push(
        vscode.commands.registerCommand('autopromo.refreshCampaign', () => campaignProvider.refresh()),
        vscode.commands.registerCommand('autopromo.refreshAnalytics', () => analyticsProvider.refresh())
    );
}

async function checkProjectFiles(): Promise<boolean> {
    const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
    if (!workspaceFolder) {
        return false;
    }

    const projectFiles = ['package.json', 'pyproject.toml', 'Cargo.toml', 'go.mod'];
    const basePath = workspaceFolder.uri.fsPath;

    for (const file of projectFiles) {
        if (fs.existsSync(path.join(basePath, file))) {
            return true;
        }
    }

    return false;
}

function getTerminal(): vscode.Terminal {
    const existingTerminal = vscode.window.terminals.find(t => t.name === 'AutoPromo');
    if (existingTerminal) {
        return existingTerminal;
    }

    return vscode.window.createTerminal('AutoPromo');
}

async function updateConfigurationContext() {
    const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
    if (!workspaceFolder) {
        vscode.commands.executeCommand('setContext', 'autopromo.configured', false);
        return;
    }

    const configPath = path.join(workspaceFolder.uri.fsPath, 'campaign.yaml');
    const isConfigured = fs.existsSync(configPath);
    
    vscode.commands.executeCommand('setContext', 'autopromo.configured', isConfigured);

    // Check if we have analytics data
    const statePath = path.join(workspaceFolder.uri.fsPath, '.autopromo', 'state');
    const hasData = fs.existsSync(statePath);
    vscode.commands.executeCommand('setContext', 'autopromo.hasData', hasData);
}

function getQuickStartWebviewContent(): string {
    return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AutoPromo Quick Start</title>
    <style>
        body {
            font-family: var(--vscode-font-family);
            color: var(--vscode-foreground);
            background-color: var(--vscode-editor-background);
            padding: 20px;
            line-height: 1.6;
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        
        .step {
            background: var(--vscode-editor-background);
            border: 1px solid var(--vscode-widget-border);
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
        }
        
        .step h3 {
            color: var(--vscode-textLink-foreground);
            margin-top: 0;
        }
        
        .action-button {
            background-color: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            cursor: pointer;
            margin: 5px;
        }
        
        .action-button:hover {
            background-color: var(--vscode-button-hoverBackground);
        }
        
        .code {
            background: var(--vscode-textCodeBlock-background);
            color: var(--vscode-textPreformat-foreground);
            padding: 10px;
            border-radius: 4px;
            font-family: var(--vscode-editor-font-family);
            margin: 10px 0;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 AutoPromo Quick Start</h1>
        <p>Get started with AI-powered social media promotion in minutes</p>
    </div>

    <div class="step">
        <h3>Step 1: Initialize Your Campaign</h3>
        <p>AutoPromo can automatically detect your project type and create an optimized configuration.</p>
        <button class="action-button" onclick="runCommand('autopromo.init')">
            🔍 Auto-detect & Initialize
        </button>
        <button class="action-button" onclick="runCommand('autopromo.quickStart')">
            ⚡ Quick Setup
        </button>
    </div>

    <div class="step">
        <h3>Step 2: Configure Credentials</h3>
        <p>Set up your social media API credentials securely.</p>
        <button class="action-button" onclick="runCommand('autopromo.setupCredentials')">
            🔐 Setup Credentials
        </button>
    </div>

    <div class="step">
        <h3>Step 3: Preview & Post</h3>
        <p>Generate AI content and preview before posting to your platforms.</p>
        <button class="action-button" onclick="runCommand('autopromo.plan')">
            👀 Preview Campaign
        </button>
        <button class="action-button" onclick="runCommand('autopromo.apply')">
            🚀 Execute Campaign
        </button>
    </div>

    <div class="step">
        <h3>Quick Actions</h3>
        <p>Shortcuts for common tasks:</p>
        <button class="action-button" onclick="runCommand('autopromo.quickPost')">
            💬 Quick Post
        </button>
        <button class="action-button" onclick="runCommand('autopromo.stats')">
            📊 View Analytics
        </button>
        <button class="action-button" onclick="runCommand('autopromo.openConfig')">
            ⚙️ Edit Configuration
        </button>
    </div>

    <div class="step">
        <h3>Example Configuration</h3>
        <p>Here's what a basic campaign.yaml looks like:</p>
        <div class="code">
name: "my-awesome-app"
concept: "AI-powered productivity tool"
url: "https://myapp.com"
platforms: [twitter, bluesky]
content:
  style: "casual"
  action: "Try it free!"
  hashtags: ["productivity", "AI"]
analytics: true
        </div>
    </div>

    <script>
        function runCommand(command) {
            vscode.postMessage({
                command: 'executeCommand',
                commandId: command
            });
        }
        
        const vscode = acquireVsCodeApi();
    </script>
</body>
</html>`;
}

function showPreviewPanel(previewData: any) {
    const panel = vscode.window.createWebviewPanel(
        'autoPromoPreview',
        'Campaign Preview',
        vscode.ViewColumn.Two,
        {
            enableScripts: true
        }
    );

    panel.webview.html = getPreviewWebviewContent(previewData);
}

function getPreviewWebviewContent(previewData: any): string {
    const platforms = Object.keys(previewData.content || {});
    
    const platformPreviews = platforms.map(platform => {
        const content = previewData.content[platform];
        return `
            <div class="platform-preview">
                <h3>${platform.charAt(0).toUpperCase() + platform.slice(1)}</h3>
                <div class="content-preview">
                    ${content.text || 'No content generated'}
                </div>
                ${content.media ? `<div class="media-info">📷 Media: ${content.media.length} file(s)</div>` : ''}
            </div>
        `;
    }).join('');

    return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Campaign Preview</title>
    <style>
        body {
            font-family: var(--vscode-font-family);
            color: var(--vscode-foreground);
            background-color: var(--vscode-editor-background);
            padding: 20px;
            line-height: 1.6;
        }
        
        .platform-preview {
            background: var(--vscode-editor-background);
            border: 1px solid var(--vscode-widget-border);
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
        }
        
        .platform-preview h3 {
            color: var(--vscode-textLink-foreground);
            margin-top: 0;
        }
        
        .content-preview {
            background: var(--vscode-input-background);
            border: 1px solid var(--vscode-input-border);
            border-radius: 4px;
            padding: 15px;
            white-space: pre-wrap;
            font-size: 16px;
            line-height: 1.4;
        }
        
        .media-info {
            margin-top: 10px;
            color: var(--vscode-descriptionForeground);
            font-style: italic;
        }
        
        .execute-button {
            background-color: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
            border: none;
            padding: 12px 24px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
            margin-top: 20px;
        }
        
        .execute-button:hover {
            background-color: var(--vscode-button-hoverBackground);
        }
    </style>
</head>
<body>
    <h1>📋 Campaign Preview</h1>
    <p>Review your generated content before posting:</p>
    
    ${platformPreviews}
    
    <button class="execute-button" onclick="executeCommand()">
        🚀 Execute Campaign
    </button>
    
    <script>
        function executeCommand() {
            vscode.postMessage({
                command: 'executeCommand',
                commandId: 'autopromo.apply'
            });
        }
        
        const vscode = acquireVsCodeApi();
    </script>
</body>
</html>`;
}

function showAnalyticsPanel(statsData: any) {
    const panel = vscode.window.createWebviewPanel(
        'autoPromoAnalytics',
        'AutoPromo Analytics',
        vscode.ViewColumn.Two,
        {
            enableScripts: true
        }
    );

    panel.webview.html = getAnalyticsWebviewContent(statsData);
}

function getAnalyticsWebviewContent(statsData: any): string {
    return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AutoPromo Analytics</title>
    <style>
        body {
            font-family: var(--vscode-font-family);
            color: var(--vscode-foreground);
            background-color: var(--vscode-editor-background);
            padding: 20px;
            line-height: 1.6;
        }
        
        .metric-card {
            background: var(--vscode-editor-background);
            border: 1px solid var(--vscode-widget-border);
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
        }
        
        .metric-value {
            font-size: 32px;
            font-weight: bold;
            color: var(--vscode-textLink-foreground);
        }
        
        .metric-label {
            color: var(--vscode-descriptionForeground);
            margin-top: 5px;
        }
        
        .chart-placeholder {
            height: 200px;
            background: var(--vscode-input-background);
            border: 1px solid var(--vscode-input-border);
            border-radius: 4px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--vscode-descriptionForeground);
        }
    </style>
</head>
<body>
    <h1>📊 Analytics Dashboard</h1>
    
    <div class="metric-card">
        <div class="metric-value">${statsData.totalPosts || 0}</div>
        <div class="metric-label">Total Posts</div>
    </div>
    
    <div class="metric-card">
        <div class="metric-value">${statsData.totalEngagement || 0}</div>
        <div class="metric-label">Total Engagement</div>
    </div>
    
    <div class="metric-card">
        <div class="metric-value">${statsData.totalReach || 0}</div>
        <div class="metric-label">Total Reach</div>
    </div>
    
    <div class="metric-card">
        <h3>Performance Over Time</h3>
        <div class="chart-placeholder">
            Chart visualization would go here
        </div>
    </div>
</body>
</html>`;
}

// Tree Data Providers
class CampaignStatusProvider implements vscode.TreeDataProvider<CampaignItem> {
    private _onDidChangeTreeData: vscode.EventEmitter<CampaignItem | undefined | null | void> = new vscode.EventEmitter<CampaignItem | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<CampaignItem | undefined | null | void> = this._onDidChangeTreeData.event;

    refresh(): void {
        this._onDidChangeTreeData.fire();
    }

    getTreeItem(element: CampaignItem): vscode.TreeItem {
        return element;
    }

    getChildren(element?: CampaignItem): Thenable<CampaignItem[]> {
        if (!element) {
            return Promise.resolve(this.getCampaignStatus());
        }
        return Promise.resolve([]);
    }

    private getCampaignStatus(): CampaignItem[] {
        const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
        if (!workspaceFolder) {
            return [];
        }

        const configPath = path.join(workspaceFolder.uri.fsPath, 'campaign.yaml');
        
        if (!fs.existsSync(configPath)) {
            return [new CampaignItem('Not Configured', vscode.TreeItemCollapsibleState.None, 'warning')];
        }

        // In a real implementation, you would parse the YAML and show actual status
        return [
            new CampaignItem('Campaign: Configured', vscode.TreeItemCollapsibleState.None, 'success'),
            new CampaignItem('Platforms: Twitter, Bluesky', vscode.TreeItemCollapsibleState.None, 'info'),
            new CampaignItem('Status: Ready', vscode.TreeItemCollapsibleState.None, 'success'),
        ];
    }
}

class QuickActionsProvider implements vscode.TreeDataProvider<ActionItem> {
    private _onDidChangeTreeData: vscode.EventEmitter<ActionItem | undefined | null | void> = new vscode.EventEmitter<ActionItem | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<ActionItem | undefined | null | void> = this._onDidChangeTreeData.event;

    refresh(): void {
        this._onDidChangeTreeData.fire();
    }

    getTreeItem(element: ActionItem): vscode.TreeItem {
        return element;
    }

    getChildren(element?: ActionItem): Thenable<ActionItem[]> {
        if (!element) {
            return Promise.resolve([
                new ActionItem('🚀 Initialize', 'autopromo.init'),
                new ActionItem('👀 Preview Campaign', 'autopromo.plan'),
                new ActionItem('✅ Execute Campaign', 'autopromo.apply'),
                new ActionItem('💬 Quick Post', 'autopromo.quickPost'),
                new ActionItem('📊 View Analytics', 'autopromo.stats'),
                new ActionItem('⚙️ Open Config', 'autopromo.openConfig'),
            ]);
        }
        return Promise.resolve([]);
    }
}

class AnalyticsProvider implements vscode.TreeDataProvider<AnalyticsItem> {
    private _onDidChangeTreeData: vscode.EventEmitter<AnalyticsItem | undefined | null | void> = new vscode.EventEmitter<AnalyticsItem | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<AnalyticsItem | undefined | null | void> = this._onDidChangeTreeData.event;

    refresh(): void {
        this._onDidChangeTreeData.fire();
    }

    getTreeItem(element: AnalyticsItem): vscode.TreeItem {
        return element;
    }

    getChildren(element?: AnalyticsItem): Thenable<AnalyticsItem[]> {
        if (!element) {
            return Promise.resolve([
                new AnalyticsItem('Total Posts: 12'),
                new AnalyticsItem('Total Engagement: 1,234'),
                new AnalyticsItem('Best Platform: Twitter'),
                new AnalyticsItem('Avg. Engagement: 103'),
            ]);
        }
        return Promise.resolve([]);
    }
}

class CampaignItem extends vscode.TreeItem {
    constructor(
        public readonly label: string,
        public readonly collapsibleState: vscode.TreeItemCollapsibleState,
        public readonly status: 'success' | 'warning' | 'error' | 'info'
    ) {
        super(label, collapsibleState);
        
        this.iconPath = new vscode.ThemeIcon(
            status === 'success' ? 'check' : 
            status === 'warning' ? 'warning' :
            status === 'error' ? 'error' : 'info'
        );
    }
}

class ActionItem extends vscode.TreeItem {
    constructor(
        public readonly label: string,
        public readonly commandId: string
    ) {
        super(label, vscode.TreeItemCollapsibleState.None);
        
        this.command = {
            command: commandId,
            title: label,
        };
    }
}

class AnalyticsItem extends vscode.TreeItem {
    constructor(
        public readonly label: string
    ) {
        super(label, vscode.TreeItemCollapsibleState.None);
    }
}

export function deactivate() {}