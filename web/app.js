document.addEventListener('DOMContentLoaded', () => {
    // Accordion Toggle
    const accordionToggle = document.getElementById('accordionToggle');
    const accordionContent = document.getElementById('accordionContent');
    
    accordionToggle.addEventListener('click', () => {
        accordionContent.classList.toggle('open');
    });

    // Custom Focus Field Toggle
    const analysisTypeSelect = document.getElementById('analysisType');
    const customFocusGroup = document.getElementById('customFocusGroup');
    
    analysisTypeSelect.addEventListener('change', (e) => {
        if (e.target.value === 'Custom Analysis') {
            customFocusGroup.style.display = 'block';
        } else {
            customFocusGroup.style.display = 'none';
        }
    });

    // Tab Switching
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            tabBtns.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.style.display = 'none');
            
            btn.classList.add('active');
            const targetTab = document.getElementById(`tab-${btn.dataset.tab}`);
            if (targetTab) targetTab.style.display = 'block';
            
            if (btn.dataset.tab === 'vault') {
                loadReportsVault();
            }
        });
    });

    // Fetch Initial System Config & Active Models
    loadSystemConfig();

    // Save Keys Button
    document.getElementById('saveKeysBtn').addEventListener('click', async () => {
        const payload = {
            openai_key: document.getElementById('openaiKey').value || null,
            anthropic_key: document.getElementById('anthropicKey').value || null,
            openrouter_key: document.getElementById('openrouterKey').value || null,
            gemini_key: document.getElementById('geminiKey').value || null,
            hf_key: document.getElementById('hfKey').value || null,
            ollama_url: document.getElementById('ollamaUrl').value || null
        };
        try {
            const resp = await fetch('/api/config', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const res = await resp.json();
            alert(res.message || 'Config saved successfully');
            loadSystemConfig();
        } catch (err) {
            alert('Error saving keys: ' + err);
        }
    });

    // Handle Form Submission
    const researchForm = document.getElementById('researchForm');
    const progressBox = document.getElementById('progressBox');
    const progressText = document.getElementById('progressText');
    const submitBtn = document.getElementById('submitBtn');
    const reportPreview = document.getElementById('reportPreview');
    const markdownSource = document.getElementById('markdownSource');

    researchForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const topic = document.getElementById('topic').value.trim();
        if (!topic) return;

        const analysisType = document.getElementById('analysisType').value;
        const customFocus = document.getElementById('customFocus').value;
        const provider = document.getElementById('provider').value;
        const formatCode = document.getElementById('formatCode').value;

        const openaiKey = document.getElementById('openaiKey').value;
        const anthropicKey = document.getElementById('anthropicKey').value;
        const openrouterKey = document.getElementById('openrouterKey').value;
        const geminiKey = document.getElementById('geminiKey').value;
        const hfKey = document.getElementById('hfKey').value;
        const ollamaUrl = document.getElementById('ollamaUrl').value;

        submitBtn.disabled = true;
        progressBox.classList.add('active');
        progressText.innerText = 'Executing 3-Layer Pipeline: Researching & Generating Topic Visual...';

        const payload = {
            topic: topic,
            analysis_type: analysisType,
            analysis_focus: analysisType === 'Custom Analysis' ? customFocus : null,
            provider: provider,
            format_code: formatCode,
            openai_key: openaiKey || null,
            anthropic_key: anthropicKey || null,
            openrouter_key: openrouterKey || null,
            gemini_key: geminiKey || null,
            hf_key: hfKey || null,
            ollama_url: ollamaUrl || null
        };

        try {
            const response = await fetch('/api/research', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.detail || 'Failed to generate report');
            }

            const data = await response.json();
            progressText.innerText = 'Report generated successfully!';
            
            // Switch to Preview tab
            document.querySelector('[data-tab="preview"]').click();

            // Populate Download Action Bar
            const actionContainer = document.getElementById('previewDownloadActions');
            const actionBar = document.getElementById('reportActionBar');
            
            if (data.output_files) {
                let badges = [];
                for (const [fmt, path] of Object.entries(data.output_files)) {
                    const cleanPath = '/' + path.replace(/\\/g, '/');
                    badges.push(`<a href="${cleanPath}" target="_blank" class="dl-badge ${fmt}">Download ${fmt.toUpperCase()}</a>`);
                }
                actionContainer.innerHTML = badges.join(' ');
                actionBar.style.display = 'flex';
            }

            // Fetch created Markdown file
            const mdPath = data.output_files.md;
            if (mdPath) {
                const mdUrl = '/' + mdPath.replace(/\\/g, '/');
                const mdResp = await fetch(mdUrl);
                const mdText = await mdResp.text();
                
                markdownSource.value = mdText;
                
                // Render HTML with marked.js
                reportPreview.innerHTML = marked.parse(mdText);
            }

        } catch (error) {
            alert('Research Error: ' + error.message);
        } finally {
            submitBtn.disabled = false;
            setTimeout(() => {
                progressBox.classList.remove('active');
            }, 3000);
        }
    });

    // Dynamic Provider Warning Check
    const providerSelect = document.getElementById('provider');
    const providerWarning = document.getElementById('providerWarning');
    const providerWarningText = document.getElementById('providerWarningText');
    let systemProviders = {};

    function updateProviderWarning() {
        const val = providerSelect.value;
        const pObj = systemProviders[val];
        
        if (val === 'ollama') {
            providerWarningText.innerHTML = "Local Ollama runs models directly on your hardware. Inference speed depends on local GPU/CPU resources and may be slower than cloud APIs.";
            providerWarning.style.display = 'block';
        } else if (pObj && !pObj.active) {
            providerWarningText.innerHTML = `Selected provider (${val.toUpperCase()}) API key is missing or unconfigured. Execution will automatically failover to local or offline models, which may increase execution time.`;
            providerWarning.style.display = 'block';
        } else {
            providerWarningText.innerHTML = "Cloud API providers require active token credits. If token credits/quota are exhausted during execution, the system will failover to local models (which may be slower).";
            providerWarning.style.display = 'block';
        }
    }

    providerSelect.addEventListener('change', updateProviderWarning);

    async function loadSystemConfig() {
        try {
            const resp = await fetch('/api/config');
            const data = await resp.json();
            systemProviders = data.providers;

            if (systemProviders.openai) document.getElementById('pill-openai').classList.toggle('active', systemProviders.openai.active);
            if (systemProviders.anthropic) document.getElementById('pill-anthropic').classList.toggle('active', systemProviders.anthropic.active);
            if (systemProviders.openrouter) document.getElementById('pill-openrouter').classList.toggle('active', systemProviders.openrouter.active);
            if (systemProviders.ollama) document.getElementById('pill-ollama').classList.toggle('active', systemProviders.ollama.active);
            if (systemProviders.gemini) document.getElementById('pill-gemini').classList.toggle('active', systemProviders.gemini.active);
            if (systemProviders.huggingface) document.getElementById('pill-hf').classList.toggle('active', systemProviders.huggingface.active);

            updateProviderWarning();
        } catch (err) {
            console.error('Failed to load system config:', err);
        }
    }

    async function loadReportsVault() {
        const reportsList = document.getElementById('reportsList');
        reportsList.innerHTML = '<li style="padding:1rem; text-align:center; color:var(--text-muted);">Loading vault reports...</li>';
        try {
            const resp = await fetch('/api/reports');
            const data = await resp.json();
            const reports = data.reports;

            if (reports.length === 0) {
                reportsList.innerHTML = '<li style="padding:1.5rem; text-align:center; color:var(--text-muted);">No reports found in history vault.</li>';
                return;
            }

            reportsList.innerHTML = reports.map(r => {
                const linksHtml = r.paths.map(p => {
                    const cleanPath = '/' + p.replace(/\\/g, '/');
                    const ext = p.split('.').pop().toLowerCase();
                    return `<a href="${cleanPath}" target="_blank" class="dl-badge ${ext}">${ext.toUpperCase()}</a>`;
                }).join(' ');

                return `
                    <li class="report-item">
                        <div>
                            <div class="report-item-title">${r.topic}</div>
                            <div class="report-item-meta">${r.analysis_focus} &bull; ${new Date(r.timestamp).toLocaleString()}</div>
                        </div>
                        <div class="download-actions">
                            ${linksHtml}
                        </div>
                    </li>
                `;
            }).join('');
        } catch (err) {
            reportsList.innerHTML = `<li style="padding:1rem; color:var(--accent-red);">Error loading reports: ${err}</li>`;
        }
    }
});
