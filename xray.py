import os
import re
import sys
import json
import webbrowser
import shutil
import tempfile
import subprocess
import datetime
import stat
import requests
from collections import defaultdict

# Force UTF-8 for Windows Consoles
sys.stdout.reconfigure(encoding='utf-8')

# 🎨 CONSOLE COLORS
class Colors:
    HEADER = '\033[95m'; BLUE = '\033[94m'; GREEN = '\033[92m'; FAIL = '\033[91m'; YELLOW = '\033[93m'; ENDC = '\033[0m'

# 🌐 CONFIGURATION
TEXT_EXTENSIONS = ('.ts', '.js', '.py', '.java', '.groovy', '.gradle', '.tsx', '.jsx', '.sh', '.yml', '.yaml', '.json', '.md', '.txt', '.xml', '.dockerfile', '.properties', '.cs', '.go', '.rb', '.php', '.rs', '.tf')

# ==========================================
# 🔑 API KEY SETUP (UPDATED FOR GITHUB ACTIONS)
# ==========================================
# This reads the secret passed from your workflow file
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print(f"{Colors.YELLOW}⚠️  Warning: GEMINI_API_KEY not found. AI features will be disabled.{Colors.ENDC}")

# 🔍 PATTERNS
IMPORT_PATTERNS = {
    'ts':  r'(?:import|export)\s+(?:[\w\s{},*]+)\s+from\s+[\'"]([^\'"]+)[\'"]|require\([\'"]([^\'"]+)[\'"]\)',
    'js':  r'(?:import|export)\s+(?:[\w\s{},*]+)\s+from\s+[\'"]([^\'"]+)[\'"]|require\([\'"]([^\'"]+)[\'"]\)',
    'py':  r'^(?:from|import)\s+([\w\.]+)',
    'java': r'^import\s+([\w\.]+);',
    'groovy': r'^import\s+([\w\.]+)',
}

RISK_PATTERNS = [
    ("🛑 Hardcoded Password", r'(password|passwd|pwd)\s*=\s*["\'][^"\']+["\']', "High", "Move to environment variables."),
    ("🛑 API Key / Secret", r'(api_key|secret|token)\s*=\s*["\'][^"\']+["\']', "Critical", "Revoke and use a Vault."),
    ("⚠️ Hardcoded Sleep", r'(time\.sleep|Thread\.sleep|await\s+page\.waitForTimeout|WebUI\.delay)', "Medium", "Use explicit waits."),
    ("⚠️ Console Log", r'(console\.log|System\.out\.print|print\(|println)', "Low", "Use a Logger."),
]

# ==========================================
# 🛠️ HELPER FUNCTIONS
# ==========================================
def handle_remove_readonly(func, path, exc):
    os.chmod(path, stat.S_IWRITE)
    func(path)

def get_file_purpose(filename, content):
    """Heuristic purpose detection (Fast & Reliable)"""
    name = filename.lower()
    if "package.json" in name: return "📦 Node.js Dependencies"
    if "pom.xml" in name: return "📦 Maven Build Config"
    if "build.gradle" in name: return "📦 Gradle Build Config"
    if "requirements.txt" in name: return "📦 Python Dependencies"
    if "docker-compose" in name: return "🐳 Docker Services"
    if "dockerfile" in name: return "🐳 Container Definition"
    if "jenkinsfile" in name: return "🤖 Jenkins Pipeline"
    if "playwright.config" in name: return "⚙️ Playwright Config"
    if "cypress.config" in name: return "⚙️ Cypress Config"
    if "readme.md" in name: return "📖 Project Documentation"
    if ".env" in name: return "🔐 Environment Config"
    if ".gitignore" in name: return "🚫 Git Ignore"
    if "test" in name or "spec" in name: return "🧪 Test Script"
    if ".java" in name: return "☕ Java Source"
    if ".py" in name: return "🐍 Python Source"
    if ".js" in name or ".ts" in name: return "📜 JS/TS Source"
    if ".groovy" in name: return "🧪 Katalon Script"
    if ".cs" in name: return "🔷 C# Source"
    return "📝 Source File"

# ==========================================
# 🧠 HYBRID INTELLIGENCE MODULE (AI + LOGIC)
# ==========================================
def generate_heuristic_readme(files_data):
    """
    Fallback method: Generates a project summary using logic (No AI required).
    """
    print(f"{Colors.YELLOW}⚠️ Gemini failed/missing. Switching to Logic Mode...{Colors.ENDC}")
    
    tech_stack = set()
    capabilities = []
    
    # Analyze file signatures
    for f, d in files_data.items():
        purpose = d['purpose']
        if "Node.js" in purpose: tech_stack.add("Node.js")
        if "Maven" in purpose: tech_stack.add("Java (Maven)")
        if "Python" in purpose: tech_stack.add("Python")
        if "Docker" in purpose: capabilities.append("Containerized (Docker)")
        if "Playwright" in purpose: capabilities.append("Browser Automation (Playwright)")
        if "Jenkins" in purpose: capabilities.append("CI/CD (Jenkins)")
    
    stack_str = ", ".join(tech_stack) if tech_stack else "Generic Codebase"
    cap_str = ", ".join(list(set(capabilities))) if capabilities else "Standard Development"
    
    return f"""
    <h3>What is this project? (Auto-Generated)</h3>
    <p>This appears to be a <strong>{stack_str}</strong> project designed for <strong>{cap_str}</strong>.</p>
    <p>It was analyzed statically without AI. The system detected {len(files_data)} files.</p>
    <ul>
        <li><strong>Tech Stack:</strong> {stack_str}</li>
        <li><strong>Key Features:</strong> {cap_str}</li>
        <li><strong>Analysis Mode:</strong> Offline / Heuristic</li>
    </ul>
    """

def generate_ai_readme(project_name, files_data):
    """Uses Google Gemini API with fallback to Heuristic."""
    
    # 1. Check Key Presence
    if not GEMINI_API_KEY:
        return generate_heuristic_readme(files_data)

    print(f"{Colors.YELLOW}🧠 Asking Gemini to explain the project...{Colors.ENDC}")
    
    file_summary = "\n".join([f"- {f}: {d['purpose']}" for f, d in list(files_data.items())[:80]]) 
    
    prompt = f"""
    You are a Technical Architect. Analyze this file list from "{project_name}".
    FILES:
    {file_summary}
    TASK:
    Write a concise "Project Overview" in HTML format (no markdown).
    1. Title: <h3>What is this project?</h3>
    2. Description: A paragraph explaining the tech stack and likely purpose.
    3. Highlights: A <ul> list of 3 key architectural features.
    Keep it under 200 words.
    """

    try:
        # UPDATED URL: Using 'gemini-2.5-flash' which is more stable
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
        headers = {'Content-Type': 'application/json'}
        data = {"contents": [{"parts": [{"text": prompt}]}]}

        response = requests.post(url, headers=headers, json=data, timeout=10)
        
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            print(f"{Colors.FAIL}❌ Gemini Error {response.status_code}: {response.text}{Colors.ENDC}")
            return generate_heuristic_readme(files_data) # Fallback on error
            
    except Exception as e:
        print(f"{Colors.FAIL}❌ Connection Failed: {e}{Colors.ENDC}")
        return generate_heuristic_readme(files_data) # Fallback on exception

# ==========================================
# 🧠 CORE SCANNER
# ==========================================
def scan_project(root_dir):
    print(f"{Colors.HEADER}🚀 ANALYZING: {root_dir}...{Colors.ENDC}")
    files_data = {}
    
    IGNORED = {'node_modules', '.git', 'venv', 'dist', 'bin', 'obj', '.idea', 'target', '.vscode'}

    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d not in IGNORED]
        
        for f in files:
            if f.endswith(TEXT_EXTENSIONS) or f in ['Dockerfile', 'Jenkinsfile']:
                path = os.path.join(root, f)
                rel_path = os.path.relpath(path, root_dir).replace('\\', '/')
                
                try:
                    with open(path, 'r', encoding='utf-8', errors='ignore') as fo:
                        lines = fo.readlines()
                        content = "".join(lines)
                        
                        risks = []
                        for rname, pat, severity, fix in RISK_PATTERNS:
                            for m in re.finditer(pat, content, re.IGNORECASE):
                                line = content.count('\n', 0, m.start()) + 1
                                risks.append({"type": rname, "line": line, "severity": severity, "fix": fix})

                        objectives = []
                        if "test" in f.lower() or "spec" in f.lower():
                            if "@Test" in content: objectives.append("Java/TestNG Test")
                            elif "test(" in content: objectives.append("JS/Playwright Test")
                            else: objectives.append("Automated Script")

                        purpose = get_file_purpose(f, content)
                        imports = []
                        ext = '.' + f.split('.')[-1]
                        key = ext[1:]
                        if key in IMPORT_PATTERNS:
                            for m in re.findall(IMPORT_PATTERNS[key], content):
                                imp = next((x for x in m if x), None)
                                if imp: imports.append(imp)

                        files_data[rel_path] = {
                            "purpose": purpose, 
                            "risks": risks, 
                            "objectives": objectives, 
                            "raw_imports": imports
                        }
                except: pass

    # Build Graph
    graph_edges = [] 
    used_by = defaultdict(set)
    for src, data in files_data.items():
        for imp in data['raw_imports']:
            tgt = imp.split('/')[-1]
            if tgt and len(tgt) > 1:
                graph_edges.append({"source": os.path.basename(src), "target": tgt})
                used_by[tgt].add(src) 

    return files_data, graph_edges, used_by

# ==========================================
# 🎨 REPORT GENERATOR
# ==========================================
def generate_report(project_name, files_data, graph_edges, used_by):
    print(f"{Colors.GREEN}🎨 Building Report...{Colors.ENDC}")
    
    # Gets AI readme OR Logic readme automatically
    ai_readme = generate_ai_readme(project_name, files_data)
    
    total_files = len(files_data)
    total_tests = sum(len(d['objectives']) for d in files_data.values())
    total_risks = sum(len(d['risks']) for d in files_data.values())
    critical_hubs = sorted(used_by.items(), key=lambda x: len(x[1]), reverse=True)[:6]

    impact_html = ""
    if critical_hubs:
        for hub, dependents in critical_hubs:
            dep_list = "".join([f"<li class='small text-muted border-bottom py-1'>{d}</li>" for d in list(dependents)[:5]])
            impact_html += f"""
            <div class="col-md-6 mb-3"><div class="card h-100 border-start border-4 border-primary shadow-sm">
                <div class="card-body">
                    <div class="d-flex justify-content-between"><strong>{hub}</strong><span class="badge bg-primary">{len(dependents)} Refs</span></div>
                    <ul class="list-unstyled mt-2 mb-0">{dep_list}</ul>
                </div>
            </div></div>"""
    else: impact_html = "<div class='alert alert-light'>No major dependencies found.</div>"

    risk_rows = ""
    for f, d in files_data.items():
        for r in d['risks']:
            badge = "bg-danger" if r['severity'] == "Critical" else "bg-warning text-dark"
            risk_rows += f"<tr><td><span class='badge {badge}'>{r['severity']}</span></td><td>{f}</td><td>{r['type']}</td><td>{r['fix']}</td></tr>"

    graph_json = json.dumps(graph_edges)

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>{project_name} - Enterprise Utility</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
        <style>
            body {{ font-family: 'Segoe UI', sans-serif; background: #f0f2f5; }}
            .sidebar {{ height: 100vh; width: 250px; position: fixed; top: 0; left: 0; background: #1a1a1a; color: white; padding: 20px; }}
            .sidebar .nav-link {{ color: #aaa; margin-bottom: 5px; }}
            .sidebar .nav-link.active {{ color: #fff; background: #333; border-radius: 5px; }}
            .main-content {{ margin-left: 250px; padding: 30px; }}
            .stat-card {{ border: none; border-radius: 10px; color: white; }}
            .mermaid {{ background: white; padding: 20px; border-radius: 10px; text-align: center; }}
            .ai-box {{ background: white; border-left: 5px solid #4285F4; padding: 20px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }}
        </style>
    </head>
    <body>
    <div class="sidebar d-flex flex-column">
        <h4 class="mb-4">⚡ QA Utility</h4>
        <ul class="nav nav-pills flex-column mb-auto" id="mainTab">
            <li class="nav-item"><a class="nav-link active" data-bs-toggle="pill" href="#dash"><i class="fas fa-chart-line me-2"></i> Dashboard</a></li>
            <li class="nav-item"><a class="nav-link" data-bs-toggle="pill" href="#readme"><i class="fas fa-magic me-2"></i> Project Overview</a></li>
            <li class="nav-item"><a class="nav-link" data-bs-toggle="pill" href="#risk"><i class="fas fa-shield-alt me-2"></i> Risks <span class="badge bg-danger ms-2">{total_risks}</span></a></li>
            <li class="nav-item"><a class="nav-link" id="arch-tab" data-bs-toggle="pill" href="#arch"><i class="fas fa-project-diagram me-2"></i> Architecture</a></li>
        </ul>
        <div class="mt-auto small text-muted">Generated: {datetime.datetime.now().strftime("%Y-%m-%d")}</div>
    </div>
    <div class="main-content"><div class="tab-content">
        <div class="tab-pane fade show active" id="dash">
            <h2>Project Dashboard</h2>
            <div class="row mb-4">
                <div class="col-md-3"><div class="card stat-card bg-primary p-3"><h3>{total_files}</h3><small>Files</small></div></div>
                <div class="col-md-3"><div class="card stat-card bg-success p-3"><h3>{total_tests}</h3><small>Tests</small></div></div>
                <div class="col-md-3"><div class="card stat-card bg-danger p-3"><h3>{total_risks}</h3><small>Risks</small></div></div>
                <div class="col-md-3"><div class="card stat-card bg-info p-3"><h3>{len(critical_hubs)}</h3><small>Hubs</small></div></div>
            </div>
            <h4>Impact Analysis</h4>
            <div class="row">{impact_html}</div>
        </div>
        <div class="tab-pane fade" id="readme">
            <h2>Project Explanation</h2>
            <div class="ai-box">{ai_readme}</div>
        </div>
        <div class="tab-pane fade" id="risk">
            <h2>Security Audit</h2>
            <div class="card"><table class="table table-hover mb-0">
                <thead><tr><th>Sev</th><th>File</th><th>Issue</th><th>Fix</th></tr></thead>
                <tbody>{risk_rows if risk_rows else "<tr><td colspan='4'>Clean code!</td></tr>"}</tbody>
            </table></div>
        </div>
        <div class="tab-pane fade" id="arch">
            <h2>Architecture</h2>
            <div class="mermaid" id="graph"></div>
        </div>
    </div></div>
    
    <script id="gdata" type="application/json">{graph_json}</script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        document.addEventListener('DOMContentLoaded', () => {{
            mermaid.initialize({{ startOnLoad: false, securityLevel: 'loose' }});
            const data = JSON.parse(document.getElementById('gdata').textContent);
            const div = document.getElementById('graph');
            
            function draw() {{
                if(!data || data.length === 0) {{ 
                    div.innerHTML = '<div class="alert alert-info">No dependencies found to graph.</div>'; 
                    return; 
                }}
                let s = "graph LR\\nclassDef f fill:#fff,stroke:#333;\\n";
                let nodes = {{}}, c = 1;
                const getSafeId = n => nodes[n] || (nodes[n] = "n" + c++);

                data.forEach(e => {{
                    let u = getSafeId(e.source);
                    let v = getSafeId(e.target);
                    let l1 = e.source.replace(/[^a-zA-Z0-9._-]/g, '_');
                    let l2 = e.target.replace(/[^a-zA-Z0-9._-]/g, '_');
                    if(u !== v) s += `${{u}}["${{l1}}"] --> ${{v}}["${{l2}}"]\\n`;
                }});
                
                div.innerHTML = s; div.removeAttribute('data-processed');
                try {{ mermaid.run({{ nodes: [div] }}); }} catch(err) {{ div.innerHTML = "Error: " + err.message; }}
            }}
            document.getElementById('arch-tab').addEventListener('shown.bs.tab', () => setTimeout(draw, 100));
        }});
    </script>
    </body></html>
    """
    
    path = "qa_report_final.html"
    with open(path, "w", encoding="utf-8") as f: f.write(html_content)
    print(f"{Colors.HEADER}✅ Done: {path}{Colors.ENDC}")
    # Commented out for headless server environments
    # webbrowser.open("file://" + os.path.abspath(path))

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "."
    path = target
    is_temp = False
    
    if "github.com" in target:
        print(f"{Colors.BLUE}⬇️ Cloning...{Colors.ENDC}")
        temp_dir = tempfile.mkdtemp()
        try:
            # Requires git to be installed on the runner
            subprocess.check_call(["git", "clone", "--depth", "1", target, temp_dir], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            path = temp_dir
            is_temp = True
        except: 
            shutil.rmtree(temp_dir, onerror=handle_remove_readonly)
            sys.exit(1)
            
    try:
        data, edges, usage = scan_project(path)
        generate_report(os.path.basename(target), data, edges, usage)
    finally:
        if is_temp: shutil.rmtree(path, onerror=handle_remove_readonly)
