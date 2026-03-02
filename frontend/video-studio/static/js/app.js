/**
 * Marketing Video Agent Factory - Frontend Application
 * Chat interface with Enhanced Brand Setup and Video Gallery
 */

class MarketingVideoApp {
    constructor() {
        this.sessionId = null;
        this.userId = 'default_user';
        this.generatedImages = [];
        this.generatedImagesMeta = {};  // Stores caption/hashtags for each image
        this.currentCaption = null;
        this.currentHashtags = [];
        
        // Campaign tracking
        this.currentCampaign = null;
        this.campaignPosts = [];  // Array of {image, caption, hashtags, day, week}
        this.galleryViewMode = 'all';  // 'all', 'posts', 'campaigns'
        
        // Brand configuration
        this.brandConfig = {
            companyName: '',
            industry: '',
            companyOverview: '',
            targetAudience: '',  // Who is the brand marketing to
            productsServices: '',  // What products/services does the brand offer
            marketingGoals: [],  // Marketing objectives (awareness, conversion, etc.)
            brandMessaging: '',  // Key messages and value propositions
            competitivePositioning: '',  // How brand stands out
            instagramLink: '',
            tone: 'professional',
            logoPath: null,
            logoFilename: null,
            brandColors: null,
            selectedPreset: null,
            selectedPalette: null,
            referenceImages: [],
            userImages: [],  // Images user wants included in videos (with usage intent)
            scrapedImages: [],
            scrapedBrandInfo: null,  // Brand info extracted from URL
            numImages: 1
        };

        // Usage intent options for user images
        this.userImageIntents = [
            { value: 'auto', label: 'Auto (AI decides)', icon: '🤖' },
            { value: 'background', label: 'Background', icon: '🖼️' },
            { value: 'product_focus', label: 'Product Focus', icon: '📦' },
            { value: 'team_people', label: 'Team/People', icon: '👥' },
            { value: 'style_reference', label: 'Style Reference', icon: '🎨' },
            { value: 'logo_badge', label: 'Logo/Badge', icon: '🏷️' }
        ];
        
        // Processing state
        this.isProcessing = false;
        
        // Preset palettes
        this.palettes = {
            sunset: { dominant: '#FF6B6B', palette: ['#FF6B6B', '#FEC89A', '#FFD93D', '#C1FFD7', '#6BCB77'] },
            ocean: { dominant: '#0077B6', palette: ['#0077B6', '#00B4D8', '#90E0EF', '#CAF0F8', '#48CAE4'] },
            forest: { dominant: '#2D6A4F', palette: ['#2D6A4F', '#40916C', '#52B788', '#95D5B2', '#B7E4C7'] },
            purple: { dominant: '#7209B7', palette: ['#7209B7', '#9D4EDD', '#C77DFF', '#E0AAFF', '#F3D5FF'] },
            coral: { dominant: '#FF6B6B', palette: ['#FF6B6B', '#F472B6', '#FB7185', '#FECDD3', '#FFF1F2'] },
            midnight: { dominant: '#6366F1', palette: ['#1A1B2E', '#2D3154', '#6366F1', '#A5B4FC', '#E0E7FF'] },
            golden: { dominant: '#DAA520', palette: ['#B8860B', '#DAA520', '#FFD700', '#FFF8DC', '#FFFACD'] },
            monochrome: { dominant: '#1A1A1A', palette: ['#1A1A1A', '#4A4A4A', '#7A7A7A', '#DADADA', '#F5F5F5'] }
        };
        
        // Preset configurations - logoFullPath and referenceImages will be set dynamically from server
        this.presets = {
            socialbunkr: {
                name: 'SocialBunkr',
                industry: 'Travel & Hospitality',
                logo: '/static/presets/socialbunkr-logo.jpeg',
                logoFullPath: null,
                colors: { dominant: '#FF6B35', palette: ['#FF6B35', '#F7C59F', '#2EC4B6', '#011627', '#FDFFFC'] },
                referenceImages: [], // Will be loaded from server
                userImages: [] // No user images for SocialBunkr preset
            },
            hylancer: {
                name: 'Hylancer',
                industry: 'Technology',
                logo: '/static/presets/hylancer-logo.jpeg',
                logoFullPath: null,
                // Hylancer brand: Yellow (#F7C001), Black, White - illustrated style
                colors: { dominant: '#F7C001', palette: ['#F7C001', '#1A1A1A', '#FFFFFF', '#2D2D2D', '#FFE066'] },
                referenceImages: [] // Will be loaded from server
            },
            technova: {
                name: 'TechNova',
                industry: 'Technology',
                logo: null,
                logoFullPath: null,
                colors: { dominant: '#0066FF', palette: ['#0066FF', '#00AAFF', '#FFFFFF', '#1A1A2E', '#E0E7FF'] },
                referenceImages: []
            }
        };
        
        // Load preset logo paths from server
        this.loadPresetPaths();
        
        this.initElements();
        this.initEventListeners();
        this.initSession();
    }
    
    async loadPresetPaths() {
        // Get the actual filesystem paths for preset logos and reference images from server
        try {
            const response = await fetch('/preset-paths');
            if (response.ok) {
                const data = await response.json();
                if (data.presets) {
                    for (const [key, value] of Object.entries(data.presets)) {
                        if (this.presets[key]) {
                            // Set logo path
                            if (value.logo_full_path) {
                                this.presets[key].logoFullPath = value.logo_full_path;
                            }
                            // Set reference images
                            if (value.reference_images && value.reference_images.length > 0) {
                                this.presets[key].referenceImages = value.reference_images;
                                console.log(`Loaded ${value.reference_images.length} reference images for ${key}`);
                            }
                        }
                    }
                }
            }
        } catch (error) {
            console.log('Could not load preset paths:', error);
        }
    }
    
    initElements() {
        // Tab elements
        this.tabBtns = document.querySelectorAll('.tab-btn');
        this.chatTab = document.getElementById('chatTab');
        this.brandTab = document.getElementById('brandTab');
        this.switchToBrandBtn = document.getElementById('switchToBrand');
        
        // Chat elements
        this.chatContainer = document.getElementById('chatContainer');
        this.chatMessages = document.getElementById('chatMessages');
        this.chatInput = document.getElementById('chatInput');
        this.sendBtn = document.getElementById('sendBtn');
        
        // Brand form elements
        this.brandForm = document.getElementById('brandForm');
        this.presetCards = document.querySelectorAll('.preset-card');
        this.uploadZone = document.getElementById('uploadZone');
        this.logoInput = document.getElementById('logoInput');
        this.uploadContent = document.getElementById('uploadContent');
        this.uploadPreview = document.getElementById('uploadPreview');
        this.logoPreview = document.getElementById('logoPreview');
        this.removeLogo = document.getElementById('removeLogo');
        this.colorExtraction = document.getElementById('colorExtraction');
        this.extractionLoading = document.getElementById('extractionLoading');
        this.colorPalette = document.getElementById('colorPalette');
        this.colorSwatches = document.getElementById('colorSwatches');
        this.paletteOptions = document.querySelectorAll('.palette-option');
        this.companyNameInput = document.getElementById('companyName');
        this.industrySelect = document.getElementById('industry');
        this.companyOverviewInput = document.getElementById('companyOverview');
        this.targetAudienceInput = document.getElementById('targetAudience');
        this.productsServicesInput = document.getElementById('productsServices');
        this.marketingGoalsInputs = document.querySelectorAll('input[name="marketingGoals"]');
        this.brandMessagingInput = document.getElementById('brandMessaging');
        this.competitivePositioningInput = document.getElementById('competitivePositioning');
        this.instagramLinkInput = document.getElementById('instagramLink');
        this.scrapeInstagramBtn = document.getElementById('scrapeInstagramBtn');
        this.scrapedImagesPreview = document.getElementById('scrapedImagesPreview');
        this.scrapedImagesGrid = document.getElementById('scrapedImagesGrid');
        this.clearScrapedBtn = document.getElementById('clearScrapedBtn');
        this.toneOptions = document.querySelectorAll('input[name="tone"]');
        this.applyBrandBtn = document.getElementById('applyBrandBtn');
        
        // Reference images
        this.referenceUploadZone = document.getElementById('referenceUploadZone');
        this.referenceInput = document.getElementById('referenceInput');
        this.referenceUploadContent = document.getElementById('referenceUploadContent');
        this.referencePreviews = document.getElementById('referencePreviews');

        // User images for posts
        this.userImagesUploadZone = document.getElementById('userImagesUploadZone');
        this.userImagesInput = document.getElementById('userImagesInput');
        this.userImagesUploadContent = document.getElementById('userImagesUploadContent');
        this.userImagesPreviews = document.getElementById('userImagesPreviews');

        // Number of images
        this.numImagesSlider = document.getElementById('numImages');
        this.numImagesValue = document.getElementById('numImagesValue');
        
        // Gallery elements
        this.galleryContainer = document.getElementById('galleryContainer');
        this.contentGrid = document.getElementById('contentGrid');
        this.emptyState = document.getElementById('emptyState');
        this.galleryActions = document.getElementById('galleryActions');
        this.refreshBtn = document.getElementById('refreshBtn');
        this.downloadAllBtn = document.getElementById('downloadAllBtn');
        this.newSessionBtn = document.getElementById('newSessionBtn');
        this.galleryTabs = document.querySelectorAll('.gallery-tab');
        
        // Caption display
        this.captionDisplay = document.getElementById('captionDisplay');
        this.captionContent = document.getElementById('captionContent');
        this.hashtagsSection = document.getElementById('hashtagsSection');
        this.hashtagsList = document.getElementById('hashtagsList');
        this.copyCaption = document.getElementById('copyCaption');
        
        // Modal
        this.modal = document.getElementById('imageModal');
        this.modalImage = document.getElementById('modalImage');
        this.modalClose = document.getElementById('modalClose');
        this.modalDownload = document.getElementById('modalDownload');
        
        // Loading
        this.loadingOverlay = document.getElementById('loadingOverlay');
    }
    
    initEventListeners() {
        // Tab switching
        this.tabBtns.forEach(btn => {
            btn.addEventListener('click', () => this.switchTab(btn.dataset.tab));
        });
        this.switchToBrandBtn?.addEventListener('click', () => this.switchTab('brand'));
        
        // Chat
        this.sendBtn.addEventListener('click', () => this.sendMessage());
        this.chatInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        this.chatInput.addEventListener('input', () => this.resizeTextarea());
        
        // Presets
        this.presetCards.forEach(card => {
            card.addEventListener('click', () => this.selectPreset(card.dataset.preset));
        });
        
        // Logo upload
        this.uploadZone.addEventListener('click', () => this.logoInput.click());
        this.logoInput.addEventListener('change', (e) => this.handleLogoSelect(e));
        this.removeLogo?.addEventListener('click', (e) => {
            e.stopPropagation();
            this.clearLogo();
        });
        
        // Drag and drop
        this.uploadZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            this.uploadZone.classList.add('dragover');
        });
        this.uploadZone.addEventListener('dragleave', () => {
            this.uploadZone.classList.remove('dragover');
        });
        this.uploadZone.addEventListener('drop', (e) => {
            e.preventDefault();
            this.uploadZone.classList.remove('dragover');
            const file = e.dataTransfer.files[0];
            if (file && file.type.startsWith('image/')) {
                this.uploadLogo(file);
            }
        });
        
        // Palette selection
        this.paletteOptions.forEach(opt => {
            opt.addEventListener('click', () => this.selectPalette(opt.dataset.palette));
        });
        
        // Reference images upload
        this.referenceUploadZone?.addEventListener('click', () => this.referenceInput?.click());
        this.referenceInput?.addEventListener('change', (e) => this.handleReferenceSelect(e));
        
        // Reference drag and drop
        this.referenceUploadZone?.addEventListener('dragover', (e) => {
            e.preventDefault();
            this.referenceUploadZone.style.borderColor = 'var(--primary)';
        });
        this.referenceUploadZone?.addEventListener('dragleave', () => {
            this.referenceUploadZone.style.borderColor = '';
        });
        this.referenceUploadZone?.addEventListener('drop', (e) => {
            e.preventDefault();
            this.referenceUploadZone.style.borderColor = '';
            const files = Array.from(e.dataTransfer.files).filter(f => f.type.startsWith('image/'));
            files.forEach(file => this.addReferenceImage(file));
        });

        // User images for posts upload
        this.userImagesUploadZone?.addEventListener('click', () => this.userImagesInput?.click());
        this.userImagesInput?.addEventListener('change', (e) => this.handleUserImagesSelect(e));

        // User images drag and drop
        this.userImagesUploadZone?.addEventListener('dragover', (e) => {
            e.preventDefault();
            this.userImagesUploadZone.style.borderColor = 'var(--primary)';
        });
        this.userImagesUploadZone?.addEventListener('dragleave', () => {
            this.userImagesUploadZone.style.borderColor = '';
        });
        this.userImagesUploadZone?.addEventListener('drop', (e) => {
            e.preventDefault();
            this.userImagesUploadZone.style.borderColor = '';
            const files = Array.from(e.dataTransfer.files).filter(f => f.type.startsWith('image/'));
            files.forEach(file => this.addUserImage(file));
        });

        // Number of images slider
        this.numImagesSlider?.addEventListener('input', () => this.updateNumImages());
        
        // Instagram scraping
        this.scrapeInstagramBtn?.addEventListener('click', () => this.scrapeInstagram());
        this.clearScrapedBtn?.addEventListener('click', () => this.clearScrapedImages());
        
        // Brand form
        this.brandForm.addEventListener('submit', (e) => this.handleBrandSubmit(e));
        
        // New Session
        this.newSessionBtn?.addEventListener('click', () => {
            this.clearSession();
        });

        // Gallery
        this.refreshBtn?.addEventListener('click', () => this.refreshGallery());
        this.downloadAllBtn?.addEventListener('click', () => this.downloadAll());
        this.copyCaption?.addEventListener('click', () => this.copyToClipboard());
        
        // Gallery tabs
        this.galleryTabs?.forEach(tab => {
            tab.addEventListener('click', () => this.switchGalleryView(tab.dataset.view));
        });
        
        // Modal
        this.modalClose?.addEventListener('click', () => this.closeModal());
        this.modal?.querySelector('.modal-backdrop')?.addEventListener('click', () => this.closeModal());
        this.modalDownload?.addEventListener('click', () => this.downloadCurrentImage());
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && !this.modal.hidden) {
                this.closeModal();
            }
        });
    }
    
    async initSession() {
        try {
            // Check if we have a saved session
            const savedSession = localStorage.getItem('content_studio_session');
            const savedMessages = localStorage.getItem('content_studio_messages');
            
            if (savedSession) {
                // Try to resume the existing session
                const sessionData = JSON.parse(savedSession);
                const response = await fetch(`/sessions/${sessionData.session_id}`, { method: 'GET' });
                
                if (response.ok) {
                    // Session still valid, restore it
                    this.sessionId = sessionData.session_id;
                    
                    // Restore chat messages (already formatted HTML)
                    if (savedMessages) {
                        const messages = JSON.parse(savedMessages);
                        messages.forEach(msg => {
                            // Pass isPreformatted=true since content is already HTML
                            this.addMessage(msg.content, msg.role === 'user' ? 'user' : 'assistant', false, true);
                        });
                    }
                    
                    // Restore generated images
                    this.restoreImagesFromStorage();
                    
                    console.log('Session restored:', this.sessionId);
                    return;
                }
            }
            
            // Create a new session
            const response = await fetch('/sessions', { method: 'POST' });
            const data = await response.json();
            this.sessionId = data.session_id;
            
            // Save to localStorage
            localStorage.setItem('content_studio_session', JSON.stringify({
                session_id: this.sessionId,
                created: Date.now()
            }));
            
            // Clear old data for new session - start fresh
            localStorage.removeItem('content_studio_messages');
            localStorage.removeItem('content_studio_images');
            
            // Also clear the gallery UI for the new session
            this.generatedImages = [];
            this.generatedImagesMeta = {};
            this.contentGrid.innerHTML = '';
            this.emptyState.hidden = false;
            
        } catch (error) {
            console.error('Session init error:', error);
            this.sessionId = 'fallback-' + Date.now();
        }
    }
    
    // Save messages to localStorage for persistence
    saveMessagesToStorage() {
        const messages = [];
        this.chatMessages.querySelectorAll('.message').forEach(msg => {
            const isUser = msg.classList.contains('user');
            const content = msg.querySelector('.message-text')?.innerHTML || '';
            if (content) {
                messages.push({ role: isUser ? 'user' : 'assistant', content });
            }
        });
        localStorage.setItem('content_studio_messages', JSON.stringify(messages));
    }
    
    // Save generated images to localStorage for persistence
    saveImagesToStorage() {
        // Save image metadata along with paths
        localStorage.setItem('content_studio_images', JSON.stringify(this.generatedImages));
        localStorage.setItem('content_studio_images_meta', JSON.stringify(this.generatedImagesMeta || {}));
    }

    // Restore generated images from localStorage
    restoreImagesFromStorage() {
        const savedImages = localStorage.getItem('content_studio_images');
        const savedMeta = localStorage.getItem('content_studio_images_meta');

        // Load metadata
        if (savedMeta) {
            try {
                this.generatedImagesMeta = JSON.parse(savedMeta);
            } catch (e) {
                this.generatedImagesMeta = {};
            }
        } else {
            this.generatedImagesMeta = {};
        }

        if (savedImages) {
            try {
                const images = JSON.parse(savedImages);
                if (images && images.length > 0) {
                    this.generatedImages = [];
                    images.forEach(imgUrl => {
                        if (!this.generatedImages.includes(imgUrl)) {
                            this.generatedImages.push(imgUrl);
                            const meta = this.generatedImagesMeta[imgUrl];
                            const isVideo = /\.(mp4|webm|mov)$/i.test(imgUrl);

                            if (isVideo) {
                                // Restore video cards with caption/hashtags
                                const caption = meta ? (meta.caption || '') : '';
                                const hashtags = meta ? (meta.hashtags || []) : [];
                                this.addVideoToGalleryWithCaption(imgUrl, caption, hashtags);
                            } else if (meta && (meta.caption || (meta.hashtags && meta.hashtags.length > 0))) {
                                this.addImageToGalleryWithCaption(imgUrl, meta.caption || '', meta.hashtags || []);
                            } else {
                                this.addImageToGallery(imgUrl);
                            }
                        }
                    });
                }
            } catch (e) {
                console.error('Failed to restore images:', e);
            }
        }
    }
    
    // Get the most recently generated image path (for editing context)
    getLastGeneratedImage() {
        if (this.generatedImages.length > 0) {
            // Return the last (most recent) image
            return this.generatedImages[this.generatedImages.length - 1];
        }
        return null;
    }
    
    // Clear session and start fresh
    clearSession() {
        localStorage.removeItem('content_studio_session');
        localStorage.removeItem('content_studio_messages');
        localStorage.removeItem('content_studio_images');
        localStorage.removeItem('content_studio_images_meta');
        this.sessionId = null;
        this.chatMessages.innerHTML = '';
        this.generatedImages = [];
        this.generatedImagesMeta = {};
        this.contentGrid.innerHTML = '';
        this.emptyState.hidden = false;
        this.contentGrid.hidden = true;
        this.initSession();
    }
    
    switchTab(tabName) {
        this.tabBtns.forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === tabName);
        });
        
        this.chatTab.classList.toggle('active', tabName === 'chat');
        this.brandTab.classList.toggle('active', tabName === 'brand');
    }
    
    selectPreset(presetId) {
        const preset = this.presets[presetId];
        if (!preset) return;
        
        // Toggle selection
        if (this.brandConfig.selectedPreset === presetId) {
            // Deselect
            this.brandConfig.selectedPreset = null;
            this.presetCards.forEach(card => card.classList.remove('active'));
            this.companyNameInput.value = '';
            this.industrySelect.value = '';
            this.clearLogo();
            this.brandConfig.referenceImages = [];
            this.renderReferencePreviews();
            return;
        }
        
        this.brandConfig.selectedPreset = presetId;
        
        // Update UI
        this.presetCards.forEach(card => {
            card.classList.toggle('active', card.dataset.preset === presetId);
        });
        
        // Fill form
        this.companyNameInput.value = preset.name;
        this.industrySelect.value = preset.industry;
        this.brandConfig.companyName = preset.name;
        this.brandConfig.industry = preset.industry;
        this.brandConfig.brandColors = preset.colors;
        
        // Show logo preview if preset has logo
        if (preset.logo) {
            this.logoPreview.src = preset.logo;
            this.uploadContent.hidden = true;
            this.uploadPreview.hidden = false;
            this.brandConfig.logoPath = preset.logo;
            this.brandConfig.logoFullPath = preset.logoFullPath;  // Use the resolved full path
            this.brandConfig.logoFilename = `preset:${presetId}`;
        }
        
        // Show colors
        this.colorExtraction.hidden = false;
        this.extractionLoading.hidden = true;
        this.colorPalette.hidden = false;
        this.displayColors(preset.colors);
        
        // Load preset reference images if available
        if (preset.referenceImages && preset.referenceImages.length > 0) {
            this.brandConfig.referenceImages = preset.referenceImages.map((ref, index) => ({
                id: `preset-ref-${index}`,
                dataUrl: ref.url,
                fullPath: ref.full_path,
                uploading: false,
                isPreset: true
            }));
            this.renderReferencePreviews();
            console.log(`Loaded ${preset.referenceImages.length} reference images for ${presetId}`);
        } else {
            this.brandConfig.referenceImages = [];
            this.renderReferencePreviews();
        }

        // Load preset user images if available (for product/post images)
        if (preset.userImages && preset.userImages.length > 0) {
            this.brandConfig.userImages = preset.userImages.map((img, index) => ({
                id: `preset-user-${index}`,
                dataUrl: img.path,
                fullPath: img.path,
                path: img.path,
                usage_intent: img.usage_intent || 'product_focus',
                uploading: false,
                isPreset: true
            }));
            this.renderUserImagesPreviews();
            console.log(`Loaded ${preset.userImages.length} user images for ${presetId}`);
        } else {
            this.brandConfig.userImages = [];
            this.renderUserImagesPreviews();
        }
        
        // Deselect palette options
        this.paletteOptions.forEach(opt => opt.classList.remove('selected'));
    }
    
    async handleLogoSelect(event) {
        const file = event.target.files[0];
        if (file) {
            await this.uploadLogo(file);
        }
    }
    
    async uploadLogo(file) {
        // Clear preset
        this.brandConfig.selectedPreset = null;
        this.presetCards.forEach(card => card.classList.remove('active'));
        
        // Show preview
        const reader = new FileReader();
        reader.onload = (e) => {
            this.logoPreview.src = e.target.result;
            this.uploadContent.hidden = true;
            this.uploadPreview.hidden = false;
        };
        reader.readAsDataURL(file);
        
        // Show loading
        this.colorExtraction.hidden = false;
        this.extractionLoading.hidden = false;
        this.colorPalette.hidden = true;
        
        // Upload to server
        const formData = new FormData();
        formData.append('file', file);
        
        try {
            const response = await fetch('/upload-logo', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.brandConfig.logoFilename = data.filename;
                this.brandConfig.logoPath = data.path;
                this.brandConfig.logoFullPath = data.full_path;  // Store full filesystem path for agent
                this.brandConfig.brandColors = data.colors;
                this.displayColors(data.colors);
            } else {
                alert('Failed to upload logo');
                this.clearLogo();
            }
        } catch (error) {
            console.error('Upload error:', error);
            alert('Failed to upload logo');
            this.clearLogo();
        }
    }
    
    displayColors(colors) {
        this.extractionLoading.hidden = true;
        this.colorPalette.hidden = false;
        this.colorSwatches.innerHTML = '';
        
        // Dominant color
        const dominantSwatch = document.createElement('div');
        dominantSwatch.className = 'color-swatch selected';
        dominantSwatch.style.backgroundColor = colors.dominant;
        dominantSwatch.title = `${colors.dominant} (Primary)`;
        dominantSwatch.addEventListener('click', () => this.selectColor(dominantSwatch, colors.dominant));
        this.colorSwatches.appendChild(dominantSwatch);
        
        // Palette colors
        colors.palette.forEach(color => {
            if (color !== colors.dominant) {
                const swatch = document.createElement('div');
                swatch.className = 'color-swatch';
                swatch.style.backgroundColor = color;
                swatch.title = color;
                swatch.addEventListener('click', () => this.selectColor(swatch, color));
                this.colorSwatches.appendChild(swatch);
            }
        });
    }
    
    selectColor(swatch, color) {
        this.colorSwatches.querySelectorAll('.color-swatch').forEach(s => s.classList.remove('selected'));
        swatch.classList.add('selected');
        
        if (this.brandConfig.brandColors) {
            this.brandConfig.brandColors.dominant = color;
        }
        
        // Deselect palette options
        this.paletteOptions.forEach(opt => opt.classList.remove('selected'));
        this.brandConfig.selectedPalette = null;
    }
    
    selectPalette(paletteName) {
        const palette = this.palettes[paletteName];
        if (!palette) return;
        
        this.brandConfig.brandColors = { ...palette };
        this.brandConfig.selectedPalette = paletteName;
        
        // Update UI
        this.paletteOptions.forEach(opt => {
            opt.classList.toggle('selected', opt.dataset.palette === paletteName);
        });
        
        // Show colors
        this.colorExtraction.hidden = false;
        this.extractionLoading.hidden = true;
        this.colorPalette.hidden = false;
        this.displayColors(palette);
    }
    
    clearLogo() {
        this.logoInput.value = '';
        this.brandConfig.logoFilename = null;
        this.brandConfig.logoPath = null;
        this.uploadContent.hidden = false;
        this.uploadPreview.hidden = true;
        this.colorExtraction.hidden = true;
        
        // Don't clear colors if from palette
        if (!this.brandConfig.selectedPalette) {
            this.brandConfig.brandColors = null;
        }
    }
    
    // Reference images handling
    handleReferenceSelect(event) {
        const files = Array.from(event.target.files);
        files.forEach(file => this.addReferenceImage(file));
    }
    
    async addReferenceImage(file) {
        if (this.brandConfig.referenceImages.length >= 5) {
            alert('Maximum 5 reference images allowed');
            return;
        }
        
        // Create preview immediately for UX
        const reader = new FileReader();
        reader.onload = async (e) => {
            const refData = {
                id: 'ref-' + Date.now(),
                dataUrl: e.target.result,
                file: file,
                uploading: true,
                fullPath: null
            };
            this.brandConfig.referenceImages.push(refData);
            this.renderReferencePreviews();
            
            // Upload to server
            try {
                const formData = new FormData();
                formData.append('file', file);
                
                const response = await fetch('/upload-reference', {
                    method: 'POST',
                    body: formData
                });
                
                if (response.ok) {
                    const data = await response.json();
                    // Update the reference with the server path
                    refData.fullPath = data.full_path;
                    refData.serverPath = data.path;
                    refData.uploading = false;
                    this.renderReferencePreviews();
                } else {
                    console.error('Failed to upload reference image');
                    refData.uploading = false;
                    refData.error = true;
                    this.renderReferencePreviews();
                }
            } catch (error) {
                console.error('Error uploading reference image:', error);
                refData.uploading = false;
                refData.error = true;
                this.renderReferencePreviews();
            }
        };
        reader.readAsDataURL(file);
    }
    
    renderReferencePreviews() {
        if (!this.referencePreviews) return;
        
        if (this.brandConfig.referenceImages.length === 0) {
            this.referencePreviews.hidden = true;
            this.referenceUploadContent.hidden = false;
            return;
        }
        
        this.referencePreviews.hidden = false;
        this.referenceUploadContent.hidden = true;
        this.referencePreviews.innerHTML = '';
        
        this.brandConfig.referenceImages.forEach(ref => {
            const thumb = document.createElement('div');
            thumb.className = 'reference-thumb';
            thumb.innerHTML = `
                <img src="${ref.dataUrl}" alt="Reference">
                <button class="remove-ref" data-id="${ref.id}">×</button>
            `;
            thumb.querySelector('.remove-ref').addEventListener('click', (e) => {
                e.stopPropagation();
                this.removeReferenceImage(ref.id);
            });
            this.referencePreviews.appendChild(thumb);
        });
        
        // Add "+" button if less than 5
        if (this.brandConfig.referenceImages.length < 5) {
            const addMore = document.createElement('div');
            addMore.className = 'reference-thumb add-more';
            addMore.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 5v14M5 12h14"/></svg>`;
            addMore.style.cssText = 'display:flex;align-items:center;justify-content:center;background:var(--secondary-lighter);cursor:pointer;';
            addMore.addEventListener('click', (e) => {
                e.stopPropagation();
                this.referenceInput.click();
            });
            this.referencePreviews.appendChild(addMore);
        }
    }
    
    removeReferenceImage(id) {
        this.brandConfig.referenceImages = this.brandConfig.referenceImages.filter(r => r.id !== id);
        this.renderReferencePreviews();
    }

    // User images for posts handling
    handleUserImagesSelect(event) {
        const files = Array.from(event.target.files);
        files.forEach(file => this.addUserImage(file));
    }

    async addUserImage(file) {
        if (this.brandConfig.userImages.length >= 10) {
            alert('Maximum 10 user images allowed');
            return;
        }

        // Create preview immediately for UX
        const reader = new FileReader();
        reader.onload = async (e) => {
            const imgData = {
                id: 'user-img-' + Date.now() + '-' + Math.random().toString(36).substr(2, 5),
                filename: file.name,
                dataUrl: e.target.result,
                file: file,
                uploading: true,
                fullPath: null,
                serverPath: null,
                usage_intent: 'auto',  // Default: let AI decide
                extracted_colors: [],
                dimensions: null
            };
            this.brandConfig.userImages.push(imgData);
            this.renderUserImagesPreviews();

            // Upload to server
            try {
                const formData = new FormData();
                formData.append('file', file);
                formData.append('session_id', this.sessionId || '');
                formData.append('usage_intent', imgData.usage_intent);

                const response = await fetch('/upload-user-image', {
                    method: 'POST',
                    body: formData
                });

                if (response.ok) {
                    const data = await response.json();
                    if (data.success && data.image) {
                        // Update with server data
                        imgData.id = data.image.id;
                        imgData.fullPath = data.image.path;
                        imgData.serverPath = data.image.url;
                        imgData.extracted_colors = data.image.extracted_colors || [];
                        imgData.dimensions = data.image.dimensions || null;
                        imgData.uploading = false;
                        this.renderUserImagesPreviews();
                    }
                } else {
                    console.error('Failed to upload user image');
                    imgData.uploading = false;
                    imgData.error = true;
                    this.renderUserImagesPreviews();
                }
            } catch (error) {
                console.error('Error uploading user image:', error);
                imgData.uploading = false;
                imgData.error = true;
                this.renderUserImagesPreviews();
            }
        };
        reader.readAsDataURL(file);
    }

    renderUserImagesPreviews() {
        if (!this.userImagesPreviews) return;

        if (this.brandConfig.userImages.length === 0) {
            this.userImagesPreviews.hidden = true;
            this.userImagesUploadContent.hidden = false;
            return;
        }

        this.userImagesPreviews.hidden = false;
        this.userImagesUploadContent.hidden = true;
        this.userImagesPreviews.innerHTML = '';

        this.brandConfig.userImages.forEach(img => {
            const thumb = document.createElement('div');
            thumb.className = 'user-image-thumb';
            thumb.innerHTML = `
                <div class="user-image-preview">
                    <img src="${img.dataUrl}" alt="User image">
                    ${img.uploading ? '<div class="upload-spinner"><div class="spinner-small"></div></div>' : ''}
                    ${img.error ? '<div class="upload-error">!</div>' : ''}
                    <button class="remove-user-img" data-id="${img.id}" title="Remove">×</button>
                </div>
                <div class="user-image-intent">
                    <select class="intent-select" data-id="${img.id}">
                        ${this.userImageIntents.map(intent =>
                            `<option value="${intent.value}" ${img.usage_intent === intent.value ? 'selected' : ''}>${intent.icon} ${intent.label}</option>`
                        ).join('')}
                    </select>
                </div>
            `;

            // Remove button handler
            thumb.querySelector('.remove-user-img').addEventListener('click', (e) => {
                e.stopPropagation();
                this.removeUserImage(img.id);
            });

            // Intent selector handler
            thumb.querySelector('.intent-select').addEventListener('change', (e) => {
                e.stopPropagation();
                this.updateUserImageIntent(img.id, e.target.value);
            });

            this.userImagesPreviews.appendChild(thumb);
        });

        // Add "+" button if less than 10
        if (this.brandConfig.userImages.length < 10) {
            const addMore = document.createElement('div');
            addMore.className = 'user-image-thumb add-more';
            addMore.innerHTML = `
                <div class="add-more-content">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 5v14M5 12h14"/></svg>
                    <span>Add more</span>
                </div>
            `;
            addMore.addEventListener('click', (e) => {
                e.stopPropagation();
                this.userImagesInput.click();
            });
            this.userImagesPreviews.appendChild(addMore);
        }
    }

    removeUserImage(id) {
        this.brandConfig.userImages = this.brandConfig.userImages.filter(img => img.id !== id);
        this.renderUserImagesPreviews();

        // Also delete from server if we have session
        if (this.sessionId) {
            fetch(`/delete-user-image/${this.sessionId}/${id}`, { method: 'DELETE' })
                .catch(err => console.log('Could not delete from server:', err));
        }
    }

    updateUserImageIntent(id, intent) {
        const img = this.brandConfig.userImages.find(img => img.id === id);
        if (img) {
            img.usage_intent = intent;
        }
    }

    updateNumImages() {
        const value = parseInt(this.numImagesSlider.value);
        this.brandConfig.numImages = value;
        if (this.numImagesValue) {
            this.numImagesValue.textContent = value;
        }
    }
    
    // URL Scraping (Instagram, Pinterest, Website)
    async scrapeInstagram() {
        const link = this.instagramLinkInput?.value.trim();
        if (!link) {
            alert('Please enter a URL (Instagram, Pinterest, or website)');
            return;
        }
        
        // Detect URL type and extract identifier
        let username = link;
        let urlType = 'website';
        
        if (link.includes('instagram.com')) {
            const match = link.match(/instagram\.com\/([^\/\?]+)/);
            if (match) username = match[1];
            username = username.replace('@', '');
            urlType = 'instagram';
        } else if (link.includes('pinterest.com')) {
            urlType = 'pinterest';
        } else if (link.startsWith('@')) {
            username = link.replace('@', '');
            urlType = 'instagram';
        }
        
        this.brandConfig.instagramLink = link;
        this.brandConfig.referenceUrlType = urlType;
        
        // Show loading state
        this.scrapeInstagramBtn.disabled = true;
        this.scrapeInstagramBtn.innerHTML = `
            <div class="spinner-small"></div>
            Scraping...
        `;
        
        try {
            const response = await fetch('/scrape-instagram', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username: username, limit: 6 })
            });
            
            const data = await response.json();
            
            // Store brand info if extracted
            if (data.brand_info && data.brand_info.status === 'success') {
                this.brandConfig.scrapedBrandInfo = data.brand_info;
                console.log('📊 Brand info extracted:', data.brand_info);
                
                // Auto-fill company name if empty
                const brandName = data.brand_info.brand_info?.name;
                if (brandName && !this.companyNameInput.value) {
                    this.companyNameInput.value = brandName;
                    this.brandConfig.companyName = brandName;
                }
                
                // Use extracted colors if no palette selected
                const extractedColors = data.brand_info.brand_info?.extracted_colors;
                if (extractedColors && extractedColors.length > 0 && !this.brandConfig.selectedPalette) {
                    console.log('🎨 Using extracted colors:', extractedColors);
                }
            }
            
            if (data.images && data.images.length > 0) {
                this.brandConfig.scrapedImages = data.images;
                this.renderScrapedImages();
                
                // Add scraped images to reference images
                data.images.forEach((img, index) => {
                    if (this.brandConfig.referenceImages.length < 5) {
                        this.brandConfig.referenceImages.push({
                            id: `scraped-${index}`,
                            dataUrl: img.url,
                            fullPath: img.full_path,
                            isScraped: true
                        });
                    }
                });
                this.renderReferencePreviews();
            }
            
            // Show appropriate message
            if (data.success) {
                if (data.images?.length > 0) {
                    console.log(`✅ Scraped ${data.images.length} images and brand info`);
                } else {
                    alert(data.message || 'Brand info saved. Please upload reference images manually.');
                }
            } else {
                alert(data.message || 'Could not fetch from this URL. Please try again.');
            }
        } catch (error) {
            console.error('Error scraping Instagram:', error);
            alert('Failed to scrape Instagram. Please try again.');
        } finally {
            this.scrapeInstagramBtn.disabled = false;
            this.scrapeInstagramBtn.innerHTML = `
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
                    <polyline points="17 8 12 3 7 8"/>
                    <line x1="12" y1="3" x2="12" y2="15"/>
                </svg>
                Fetch
            `;
        }
    }
    
    renderScrapedImages() {
        if (!this.scrapedImagesGrid || this.brandConfig.scrapedImages.length === 0) {
            if (this.scrapedImagesPreview) this.scrapedImagesPreview.hidden = true;
            return;
        }
        
        this.scrapedImagesPreview.hidden = false;
        this.scrapedImagesGrid.innerHTML = '';
        
        this.brandConfig.scrapedImages.forEach((img, index) => {
            const thumb = document.createElement('div');
            thumb.className = 'scraped-image-thumb selected';
            thumb.innerHTML = `<img src="${img.url}" alt="Scraped reference ${index + 1}">`;
            thumb.addEventListener('click', () => {
                thumb.classList.toggle('selected');
                // Update reference images based on selection
                this.updateScrapedSelection();
            });
            this.scrapedImagesGrid.appendChild(thumb);
        });
    }
    
    updateScrapedSelection() {
        const thumbs = this.scrapedImagesGrid?.querySelectorAll('.scraped-image-thumb');
        const selectedScraped = [];
        
        thumbs?.forEach((thumb, index) => {
            if (thumb.classList.contains('selected') && this.brandConfig.scrapedImages[index]) {
                selectedScraped.push(this.brandConfig.scrapedImages[index]);
            }
        });
        
        // Update reference images - remove old scraped, add new selected
        this.brandConfig.referenceImages = this.brandConfig.referenceImages.filter(r => !r.isScraped);
        selectedScraped.forEach((img, index) => {
            if (this.brandConfig.referenceImages.length < 5) {
                this.brandConfig.referenceImages.push({
                    id: `scraped-${index}`,
                    dataUrl: img.url,
                    fullPath: img.full_path,
                    isScraped: true
                });
            }
        });
        this.renderReferencePreviews();
    }
    
    clearScrapedImages() {
        this.brandConfig.scrapedImages = [];
        this.brandConfig.referenceImages = this.brandConfig.referenceImages.filter(r => !r.isScraped);
        if (this.scrapedImagesPreview) this.scrapedImagesPreview.hidden = true;
        if (this.instagramLinkInput) this.instagramLinkInput.value = '';
        this.renderReferencePreviews();
    }
    
    handleBrandSubmit(e) {
        e.preventDefault();
        
        // Save brand config
        this.brandConfig.companyName = this.companyNameInput.value;
        this.brandConfig.industry = this.industrySelect.value;
        this.brandConfig.companyOverview = this.companyOverviewInput?.value || '';
        this.brandConfig.targetAudience = this.targetAudienceInput?.value || '';
        this.brandConfig.productsServices = this.productsServicesInput?.value || '';
        this.brandConfig.marketingGoals = Array.from(this.marketingGoalsInputs || [])
            .filter(cb => cb.checked)
            .map(cb => cb.value);
        this.brandConfig.brandMessaging = this.brandMessagingInput?.value || '';
        this.brandConfig.competitivePositioning = this.competitivePositioningInput?.value || '';
        this.brandConfig.instagramLink = this.instagramLinkInput?.value || '';
        this.brandConfig.tone = document.querySelector('input[name="tone"]:checked')?.value || 'professional';
        this.brandConfig.numImages = parseInt(this.numImagesSlider?.value || 1);

        // Build context message parts
        const parts = [];
        if (this.brandConfig.companyName) parts.push(this.brandConfig.companyName);
        if (this.brandConfig.industry) parts.push(`(${this.brandConfig.industry})`);
        if (this.brandConfig.companyOverview) parts.push('Overview: ✓');
        if (this.brandConfig.targetAudience) parts.push('Target Audience: ✓');
        if (this.brandConfig.productsServices) parts.push('Products: ✓');
        if (this.brandConfig.logoPath) parts.push('Logo: ✓');
        if (this.brandConfig.brandColors) parts.push(`Colors: ${this.brandConfig.brandColors.dominant}`);
        parts.push(`Style: ${this.brandConfig.tone}`);
        if (this.brandConfig.referenceImages.length > 0) parts.push(`${this.brandConfig.referenceImages.length} reference image(s)`);
        if (this.brandConfig.userImages.length > 0) parts.push(`${this.brandConfig.userImages.length} image(s) for posts`);
        parts.push(`Generate: ${this.brandConfig.numImages} image(s)`);
        
        // Switch to chat and add message
        this.switchTab('chat');
        this.addMessage(`I've set up my brand: ${parts.join('. ')}`, 'user');
        
        // Send to agent
        this.sendBrandContext();
    }
    
    async sendBrandContext() {
        this.showProcessingIndicator();
        
        // Build brand info for agent
        let brandInfo = `Brand information:
- Company: ${this.brandConfig.companyName || 'Not specified'}
- Industry: ${this.brandConfig.industry || 'General'}
- Tone: ${this.brandConfig.tone || 'creative'}
- Number of images to generate: ${this.brandConfig.numImages}`;

        if (this.brandConfig.companyOverview) {
            brandInfo += `\n- Company Overview: ${this.brandConfig.companyOverview}`;
        }

        if (this.brandConfig.targetAudience) {
            brandInfo += `\n- TARGET AUDIENCE: ${this.brandConfig.targetAudience}`;
        }

        if (this.brandConfig.productsServices) {
            brandInfo += `\n- PRODUCTS/SERVICES: ${this.brandConfig.productsServices}`;
        }

        if (this.brandConfig.marketingGoals && this.brandConfig.marketingGoals.length > 0) {
            brandInfo += `\n- MARKETING_GOALS: ${this.brandConfig.marketingGoals.join(', ')}`;
        }

        if (this.brandConfig.brandMessaging) {
            brandInfo += `\n- BRAND_MESSAGING: ${this.brandConfig.brandMessaging}`;
        }

        if (this.brandConfig.competitivePositioning) {
            brandInfo += `\n- Competitive Positioning: ${this.brandConfig.competitivePositioning}`;
        }
        
        if (this.brandConfig.brandColors) {
            brandInfo += `\n- Brand Colors: Primary=${this.brandConfig.brandColors.dominant}, Palette=${this.brandConfig.brandColors.palette.join(', ')}`;
        }
        
        if (this.brandConfig.logoPath) {
            brandInfo += `\n- Logo: ${this.brandConfig.logoPath}`;
        }
        
        if (this.brandConfig.referenceImages.length > 0) {
            brandInfo += `\n- Reference images: ${this.brandConfig.referenceImages.length} image(s) provided for style inspiration`;
        }

        // Add user images info
        if (this.brandConfig.userImages.length > 0) {
            brandInfo += `\n- User images for posts: ${this.brandConfig.userImages.length} image(s) to incorporate`;
            const intentSummary = this.brandConfig.userImages.map(img =>
                `${img.filename || 'image'} (${img.usage_intent})`
            ).join(', ');
            brandInfo += `\n  Intents: ${intentSummary}`;
        }

        if (this.brandConfig.instagramLink) {
            brandInfo += `\n- Reference URL: ${this.brandConfig.instagramLink}`;
        }
        
        // Include scraped brand info if available
        if (this.brandConfig.scrapedBrandInfo) {
            const scrapedInfo = this.brandConfig.scrapedBrandInfo;
            if (scrapedInfo.brand_info) {
                const bi = scrapedInfo.brand_info;
                brandInfo += `\n\n**Extracted Brand Details from ${scrapedInfo.source || 'web'}:**`;
                if (bi.description) brandInfo += `\n- About: ${bi.description}`;
                if (bi.extracted_colors?.length) brandInfo += `\n- Colors found: ${bi.extracted_colors.join(', ')}`;
                if (bi.keywords?.length) brandInfo += `\n- Keywords: ${bi.keywords.join(', ')}`;
            }
            if (scrapedInfo.style_hints) {
                const sh = scrapedInfo.style_hints;
                brandInfo += `\n- Recommended tone: ${sh.recommended_tone || 'professional'}`;
            }
        }
        
        brandInfo += `\n\nBrand setup complete. Ready for content creation.`;
        
        // Build attachments including reference images
        const attachments = [];
        if (this.brandConfig.logoPath) {
            attachments.push({
                type: 'logo',
                path: this.brandConfig.logoPath,
                full_path: this.brandConfig.logoFullPath,
                colors: this.brandConfig.brandColors
            });
        }
        
        // Add reference images with full paths
        const uploadedRefs = this.brandConfig.referenceImages.filter(r => r.fullPath && !r.uploading);
        if (uploadedRefs.length > 0) {
            attachments.push({
                type: 'reference_images',
                count: uploadedRefs.length,
                paths: uploadedRefs.map(r => r.fullPath)
            });
        }
        
        // Add company overview
        if (this.brandConfig.companyOverview) {
            attachments.push({
                type: 'company_overview',
                content: this.brandConfig.companyOverview
            });
        }

        // Add target audience
        if (this.brandConfig.targetAudience) {
            attachments.push({
                type: 'target_audience',
                content: this.brandConfig.targetAudience
            });
        }

        // Add products/services
        if (this.brandConfig.productsServices) {
            attachments.push({
                type: 'products_services',
                content: this.brandConfig.productsServices
            });
        }

        // Add marketing goals
        if (this.brandConfig.marketingGoals && this.brandConfig.marketingGoals.length > 0) {
            attachments.push({
                type: 'marketing_goals',
                goals: this.brandConfig.marketingGoals
            });
        }

        // Add brand messaging
        if (this.brandConfig.brandMessaging) {
            attachments.push({
                type: 'brand_messaging',
                content: this.brandConfig.brandMessaging
            });
        }

        // Add competitive positioning
        if (this.brandConfig.competitivePositioning) {
            attachments.push({
                type: 'competitive_positioning',
                content: this.brandConfig.competitivePositioning
            });
        }

        // Add scraped brand info
        if (this.brandConfig.scrapedBrandInfo) {
            attachments.push({
                type: 'scraped_brand_info',
                data: this.brandConfig.scrapedBrandInfo
            });
        }

        // Add user images for posts (with usage intents)
        const uploadedUserImages = this.brandConfig.userImages.filter(img => img.fullPath && !img.uploading);
        if (uploadedUserImages.length > 0) {
            attachments.push({
                type: 'user_images',
                count: uploadedUserImages.length,
                images: uploadedUserImages.map(img => ({
                    id: img.id,
                    filename: img.filename,
                    path: img.fullPath,
                    url: img.serverPath,
                    usage_intent: img.usage_intent,
                    extracted_colors: img.extracted_colors || []
                }))
            });
        }

        // Save marketing context via API
        if (this.sessionId && (this.brandConfig.companyOverview || this.brandConfig.targetAudience || this.brandConfig.productsServices)) {
            try {
                await fetch('/upload-marketing-context', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        session_id: this.sessionId,
                        company_overview: this.brandConfig.companyOverview || '',
                        target_audience: this.brandConfig.targetAudience || '',
                        products_services: this.brandConfig.productsServices || '',
                        marketing_goals: this.brandConfig.marketingGoals || [],
                        brand_messaging: this.brandConfig.brandMessaging || '',
                        competitive_positioning: this.brandConfig.competitivePositioning || '',
                        key_differentiators: []
                    })
                });
            } catch (error) {
                console.error('Failed to save marketing context:', error);
            }
        }

        try {
            const response = await fetch('/chat/stream', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: brandInfo,
                    user_id: this.userId,
                    session_id: this.sessionId,
                    attachments: attachments,
                    num_images: this.brandConfig.numImages,
                    company_overview: this.brandConfig.companyOverview
                })
            });
            
            // Don't hide here - processStreamResponse will hide when first content arrives
            await this.processStreamResponse(response);
        } catch (error) {
            this.hideProcessingIndicator();
            this.addMessage('Brand setup saved! You can now ask me to create content for you.', 'assistant');
        }
    }
    
    resizeTextarea() {
        this.chatInput.style.height = 'auto';
        this.chatInput.style.height = Math.min(this.chatInput.scrollHeight, 100) + 'px';
    }
    
    async sendMessage() {
        const message = this.chatInput.value.trim();
        if (!message || this.isProcessing) return;
        
        this.addMessage(message, 'user');
        this.chatInput.value = '';
        this.resizeTextarea();
        
        // Build attachments from brand config
        const attachments = [];
        if (this.brandConfig.logoPath && this.brandConfig.brandColors) {
            attachments.push({
                type: 'logo',
                path: this.brandConfig.logoPath,
                full_path: this.brandConfig.logoFullPath,
                colors: this.brandConfig.brandColors
            });
        }
        
        // Add reference images with full server paths
        const uploadedRefs = this.brandConfig.referenceImages.filter(r => r.fullPath && !r.uploading);
        if (uploadedRefs.length > 0) {
            attachments.push({
                type: 'reference_images',
                count: uploadedRefs.length,
                paths: uploadedRefs.map(r => r.fullPath)  // Use full filesystem paths
            });
        }

        // Add user images for posts (with usage intents)
        const uploadedUserImages = this.brandConfig.userImages.filter(img => img.fullPath && !img.uploading);
        if (uploadedUserImages.length > 0) {
            attachments.push({
                type: 'user_images',
                count: uploadedUserImages.length,
                images: uploadedUserImages.map(img => ({
                    id: img.id,
                    filename: img.filename,
                    path: img.fullPath,
                    url: img.serverPath,
                    usage_intent: img.usage_intent,
                    extracted_colors: img.extracted_colors || []
                }))
            });
        }

        // Append brand context to message if we have it
        let fullMessage = message;
        if (this.brandConfig.companyName || this.brandConfig.brandColors) {
            fullMessage += `\n\n[Current brand context: ${this.brandConfig.companyName || 'Brand'}, Industry: ${this.brandConfig.industry || 'General'}, Tone: ${this.brandConfig.tone || 'creative'}, Colors: ${this.brandConfig.brandColors?.dominant || 'not set'}, Number of images to generate: ${this.brandConfig.numImages}]`;
            if (this.brandConfig.companyOverview) {
                fullMessage += `\n[Company Overview: ${this.brandConfig.companyOverview}]`;
            }
            if (this.brandConfig.targetAudience) {
                fullMessage += `\n[TARGET AUDIENCE: ${this.brandConfig.targetAudience}]`;
            }
            if (this.brandConfig.productsServices) {
                fullMessage += `\n[PRODUCTS/SERVICES: ${this.brandConfig.productsServices}]`;
            }
            if (this.brandConfig.marketingGoals && this.brandConfig.marketingGoals.length > 0) {
                fullMessage += `\n[MARKETING_GOALS: ${this.brandConfig.marketingGoals.join(', ')}]`;
            }
            if (this.brandConfig.brandMessaging) {
                fullMessage += `\n[BRAND_MESSAGING: ${this.brandConfig.brandMessaging}]`;
            }
        }
        
        // Show processing indicator
        this.showProcessingIndicator();
        
        try {
            const response = await fetch('/chat/stream', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: fullMessage,
                    user_id: this.userId,
                    session_id: this.sessionId,
                    attachments: attachments,
                    num_images: this.brandConfig.numImages,
                    last_generated_image: this.getLastGeneratedImage()
                })
            });
            
            // Don't hide here - processStreamResponse will hide when first content arrives
            await this.processStreamResponse(response);
        } catch (error) {
            this.hideProcessingIndicator();
            this.addMessage('Sorry, there was an error. Please try again.', 'assistant');
        }
    }
    
    showProcessingIndicator() {
        this.isProcessing = true;
        this.processingSteps = [];
        this.processingStartTime = Date.now();
        
        // Disable input
        const inputWrapper = document.querySelector('.chat-input-wrapper');
        inputWrapper?.classList.add('disabled');
        this.sendBtn.classList.add('disabled');
        
        // Add processing message to chat
        const processingDiv = document.createElement('div');
        processingDiv.className = 'agent-processing';
        processingDiv.id = 'processingIndicator';
        processingDiv.innerHTML = `
            <div class="processing-spinner"></div>
            <div class="processing-content">
                <div class="processing-title">
                    Agent is working
                    <span class="processing-dots"><span></span><span></span><span></span></span>
                </div>
                <div class="processing-subtitle" id="processingStatus">Starting up...</div>
                <div class="processing-progress">
                    <div class="progress-bar" id="processingProgressBar"></div>
                </div>
                <div class="processing-steps" id="processingSteps"></div>
                <div class="processing-time" id="processingTime">0s</div>
            </div>
        `;
        this.chatMessages.appendChild(processingDiv);
        this.scrollToBottom();
        
        // Start cycling through status messages and update timer
        this.startStatusCycle();
        this.startTimeTracker();
    }
    
    startStatusCycle() {
        const statuses = [
            { text: 'Analyzing your request...', progress: 10 },
            { text: 'Understanding context...', progress: 20 },
            { text: 'Planning response...', progress: 35 },
            { text: 'Generating content...', progress: 50 },
            { text: 'Creating visuals...', progress: 65 },
            { text: 'Refining output...', progress: 80 },
            { text: 'Almost there...', progress: 90 },
        ];
        let index = 0;
        
        this.statusInterval = setInterval(() => {
            const statusEl = document.getElementById('processingStatus');
            const progressBar = document.getElementById('processingProgressBar');
            if (statusEl && this.isProcessing) {
                const status = statuses[Math.min(index, statuses.length - 1)];
                statusEl.textContent = status.text;
                if (progressBar) {
                    progressBar.style.width = `${status.progress}%`;
                }
                if (index < statuses.length - 1) index++;
            }
        }, 2500);
    }
    
    startTimeTracker() {
        this.timeInterval = setInterval(() => {
            const timeEl = document.getElementById('processingTime');
            if (timeEl && this.isProcessing) {
                const elapsed = Math.floor((Date.now() - this.processingStartTime) / 1000);
                timeEl.textContent = `${elapsed}s`;
            }
        }, 1000);
    }
    
    updateProcessingStatus(status, tool = null) {
        const statusEl = document.getElementById('processingStatus');
        const stepsEl = document.getElementById('processingSteps');
        
        if (statusEl) {
            statusEl.textContent = status;
        }
        
        if (tool && stepsEl) {
            // Add tool step
            const step = document.createElement('div');
            step.className = 'processing-step';
            step.innerHTML = `<span class="step-icon">🔧</span> ${tool}`;
            stepsEl.appendChild(step);
            this.scrollToBottom();
        }
    }
    
    updateProcessingForVideoGeneration(statusMessage) {
        // Stop the generic status cycle — we have real status from backend
        if (this.statusInterval) {
            clearInterval(this.statusInterval);
            this.statusInterval = null;
        }

        const titleEl = document.querySelector('#processingIndicator .processing-title');
        const statusEl = document.getElementById('processingStatus');
        const progressBar = document.getElementById('processingProgressBar');

        if (titleEl) {
            titleEl.innerHTML = `
                Video Generation in Progress
                <span class="processing-dots"><span></span><span></span><span></span></span>
            `;
        }
        if (statusEl) {
            statusEl.textContent = statusMessage;
        }

        // Start a slow progress animation for video gen (40% → 95% over ~120s)
        if (progressBar && !this.videoProgressInterval) {
            let videoProgress = 40;
            progressBar.style.width = `${videoProgress}%`;

            const videoStartTime = Date.now();
            this.videoProgressInterval = setInterval(() => {
                const elapsed = Math.floor((Date.now() - videoStartTime) / 1000);

                // Slow progress: approach 95% asymptotically
                videoProgress = Math.min(95, 40 + (55 * (1 - Math.exp(-elapsed / 80))));
                progressBar.style.width = `${videoProgress}%`;

                // Update subtitle with time-based messages
                if (statusEl && this.isProcessing) {
                    if (elapsed > 90) {
                        statusEl.textContent = 'Finalizing your video...';
                    } else if (elapsed > 60) {
                        statusEl.textContent = 'Almost there — adding finishing touches...';
                    } else if (elapsed > 30) {
                        statusEl.textContent = 'Rendering frames — this takes a moment...';
                    }
                }
            }, 2000);
        }
    }

    hideProcessingIndicator() {
        this.isProcessing = false;

        // Clear status cycle
        if (this.statusInterval) {
            clearInterval(this.statusInterval);
            this.statusInterval = null;
        }

        // Clear time tracker
        if (this.timeInterval) {
            clearInterval(this.timeInterval);
            this.timeInterval = null;
        }

        // Clear video progress timer
        if (this.videoProgressInterval) {
            clearInterval(this.videoProgressInterval);
            this.videoProgressInterval = null;
        }

        // Re-enable input
        const inputWrapper = document.querySelector('.chat-input-wrapper');
        inputWrapper?.classList.remove('disabled');
        this.sendBtn.classList.remove('disabled');

        // Remove processing message
        document.getElementById('processingIndicator')?.remove();
    }
    
    async processStreamResponse(response) {
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let assistantMessage = '';
        let messageElement = null;
        let firstContentReceived = false;
        
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            const chunk = decoder.decode(value);
            const lines = chunk.split('\n');
            
            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.slice(6));
                        
                        if (data.type === 'session') {
                            this.sessionId = data.session_id;
                        } else if (data.type === 'status') {
                            // Handle status events (e.g., "Generating your video...")
                            // Do NOT hide processing indicator — video gen takes 1-2 minutes
                            // Instead, update the indicator with the real status
                            const statusMsg = data.message || 'Processing...';
                            this.updateProcessingForVideoGeneration(statusMsg);
                        } else if (data.type === 'video_generated') {
                            // Handle dedicated video generation event
                            const videoUrl = data.url;
                            if (videoUrl && !this.generatedImages.includes(videoUrl)) {
                                this.generatedImages.push(videoUrl);
                                const caption = data.caption || '';
                                const hashtags = data.hashtags || [];
                                if (caption || hashtags.length > 0) {
                                    this.addVideoToGalleryWithCaption(videoUrl, caption, hashtags);
                                } else {
                                    this.addImageToGallery(videoUrl);
                                }
                                this.saveImagesToStorage();
                            }
                        } else if (data.type === 'text') {
                            // Detect structured JSON from format_response_for_user
                            // Check for: wrapper format OR direct structured JSON
                            const contentTrimmed = data.content.trim();
                            const isStructuredContent = (
                                // Wrapper format: {'result': '...'} or {"result": "..."}
                                ((contentTrimmed.includes("{'result':") || contentTrimmed.includes('{"result":')) &&
                                 contentTrimmed.includes('has_choices')) ||
                                // Direct structured JSON: {"text": "...", "has_choices": ...}
                                (contentTrimmed.startsWith('{') && contentTrimmed.includes('"has_choices"') &&
                                 contentTrimmed.includes('"text"'))
                            );

                            if (isStructuredContent) {
                                // Try to extract structured response from this chunk
                                const structuredResponse = this.parseStructuredResponse(data.content);
                                if (structuredResponse) {
                                    // Hide processing indicator when first content arrives
                                    if (!firstContentReceived) {
                                        firstContentReceived = true;
                                        this.hideProcessingIndicator();
                                    }
                                    if (!messageElement) {
                                        messageElement = this.addMessage('', 'assistant', true);
                                    }
                                    // Use only the text from structured response, not the wrapper/JSON
                                    assistantMessage = structuredResponse.text;
                                    this.handleStructuredResponse(structuredResponse, messageElement);
                                    // Don't accumulate the wrapper text
                                    continue;
                                } else {
                                    // If we can't parse it, skip it entirely - don't display raw JSON
                                    console.log('⚠️ Skipping structured chunk that could not be parsed');
                                    continue;
                                }
                            }

                            // Hide processing indicator when first content arrives
                            if (!firstContentReceived) {
                                firstContentReceived = true;
                                this.hideProcessingIndicator();
                            }

                            // Regular text streaming
                            assistantMessage += data.content;
                            if (!messageElement) {
                                messageElement = this.addMessage('', 'assistant', true);
                            }
                            this.updateMessage(messageElement, assistantMessage);
                        } else if (data.type === 'done') {
                            // Try to parse as structured response from format_response_for_user tool
                            const structuredResponse = this.parseStructuredResponse(assistantMessage);

                            if (structuredResponse) {
                                // Handle structured response with choices
                                // Clear any accumulated wrapper text
                                if (messageElement) {
                                    messageElement.innerHTML = '';
                                }
                                this.handleStructuredResponse(structuredResponse, messageElement);
                            } else {
                                // Fallback: Handle as regular text response
                                this.parseAssistantResponse(assistantMessage);
                                this.updateRightPanel(assistantMessage);

                                // Detect and render choice buttons using text pattern matching
                                if (messageElement) {
                                    const choices = this.detectChoicesInMessage(assistantMessage);
                                    if (choices.length > 0) {
                                        const contentEl = messageElement.closest('.message')?.querySelector('.message-content');
                                        if (contentEl) {
                                            this.renderChoiceButtons(choices, contentEl);
                                        }
                                    }
                                }
                            }

                            // ALWAYS scan full message for video/media URLs
                            // (structured response text may not contain the video URL)
                            this.parseAssistantResponse(assistantMessage);
                            this.updateRightPanel(assistantMessage);

                            // Save to storage now that streaming is complete
                            this.saveMessagesToStorage();
                        }
                    } catch (e) {}
                }
            }
        }
        
        // Always ensure processing indicator is cleaned up when stream ends
        if (this.isProcessing) {
            this.hideProcessingIndicator();
        }
    }
    
    addMessage(text, role, isStreaming = false, isPreformatted = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;

        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.innerHTML = role === 'user'
            ? '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>'
            : '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M8 14s1.5 2 4 2 4-2 4-2"/><line x1="9" y1="9" x2="9.01" y2="9"/><line x1="15" y1="9" x2="15.01" y2="9"/></svg>';

        const content = document.createElement('div');
        content.className = 'message-content';

        const textDiv = document.createElement('div');
        textDiv.className = 'message-text';
        // If preformatted (restored from storage), use as-is; otherwise format
        textDiv.innerHTML = isPreformatted ? text : this.formatMessage(text);

        content.appendChild(textDiv);
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(content);

        this.chatMessages.appendChild(messageDiv);

        // For assistant messages (not streaming), detect and render choice buttons
        if (role === 'assistant' && !isStreaming) {
            const choices = this.detectChoicesInMessage(text);
            if (choices.length > 0) {
                this.renderChoiceButtons(choices, content);
            }
        }

        this.scrollToBottom();

        // Save to localStorage (but not for streaming messages which are updated later)
        if (!isStreaming) {
            this.saveMessagesToStorage();
        }

        return textDiv;
    }
    
    updateMessage(element, text) {
        element.innerHTML = this.formatMessage(text);
        this.scrollToBottom();
        // Save updated message to storage
        this.saveMessagesToStorage();
    }
    
    formatMessage(text) {
        if (!text) return '';
        
        // Skip if already contains image-link (already formatted)
        if (text.includes('class="image-link"')) {
            return text;
        }
        
        // Process image links FIRST (before code blocks), handling various formats:
        // - /generated/file.png
        // - generated/file.png  
        // - `generated/file.png`
        // - `/generated/file.png`
        let formatted = text
            // Remove backticks around image paths first
            .replace(/`((?:\/)?generated\/[^\s\`]+\.png)`/g, '$1');
        
        // Replace image paths with clickable links - handle all formats
        // Match: /generated/xxx.png or generated/xxx.png (not already in href or data-image)
        formatted = formatted.replace(/(?<!["\=\/])(?:\/)?generated\/([a-zA-Z0-9_-]+\.png)/g, (match, filename) => {
            return `<a href="/generated/${filename}" class="image-link" data-image="/generated/${filename}">📷 View Image</a>`;
        });
        
        // Then process other formatting
        return formatted
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>')
            .replace(/^### (.*?)$/gm, '<h3>$1</h3>')
            .replace(/^## (.*?)$/gm, '<h2>$1</h2>')
            .replace(/^# (.*?)$/gm, '<h1>$1</h1>')
            .replace(/^- (.*?)$/gm, '<li>$1</li>')
            .replace(/^\d+\. (.*?)$/gm, '<li>$1</li>')
            .replace(/\n/g, '<br>');
    }
    
    // Update right panel with generated content
    // ONLY show: images with captions - NOT campaign plans or regular responses
    updateRightPanel(text) {
        if (!text) return;
        
        // Only add images and their captions to the right panel
        // Campaign info stays in the chat only
        
        // Check for generated images
        const hasImage = text.includes('/generated/') || text.includes('generated/');
        
        // Extract and display hashtags if we have images
        if (hasImage) {
            const hashtagPattern = /#[a-zA-Z][a-zA-Z0-9_]*/g;
            const hashtags = text.match(hashtagPattern);
            if (hashtags && hashtags.length > 5) {
                this.displayHashtagsOnPanel(hashtags);
            }
        }
        
        // DO NOT add campaign cards, blog cards, or text content to the right panel
        // Only parseAssistantResponse will add actual images with captions
    }
    
    extractAndDisplayCaption(text) {
        // Try to extract caption content
        let caption = '';
        
        // Look for content after "Caption:" or "Instagram Caption:"
        const captionMatch = text.match(/(?:instagram\s+)?caption[:\s]*\n?([\s\S]*?)(?=\n---|\nhashtag|\n\*\*hashtag|$)/i);
        if (captionMatch && captionMatch[1]) {
            caption = captionMatch[1].trim();
            // Clean up the caption - remove markdown formatting for clean text
            caption = caption.replace(/\*\*/g, '').replace(/\*/g, '');
        }
        
        if (caption && caption.length > 20) {
            this.captionDisplay.hidden = false;
            this.captionContent.innerHTML = this.formatCaptionContent(caption);
            this.currentCaption = caption;
        }
    }
    
    formatCaptionContent(text) {
        return text
            .replace(/\n/g, '<br>')
            .replace(/✨|🚀|💡|📈|👇|🎯|🔥|💪|🌟|✅/g, '<span class="emoji">$&</span>');
    }
    
    displayHashtagsOnPanel(hashtags) {
        // Remove duplicates and limit
        const uniqueHashtags = [...new Set(hashtags)].slice(0, 30);
        
        this.hashtagsSection.hidden = false;
        this.hashtagsList.innerHTML = '';
        this.currentHashtags = uniqueHashtags;
        
        uniqueHashtags.forEach(tag => {
            const span = document.createElement('span');
            span.className = 'hashtag';
            span.textContent = tag;
            span.addEventListener('click', () => {
                navigator.clipboard.writeText(tag);
                span.classList.add('copied');
                setTimeout(() => span.classList.remove('copied'), 500);
            });
            this.hashtagsList.appendChild(span);
        });
    }
    
    addBlogCard(text) {
        this.emptyState.hidden = true;
        this.contentGrid.hidden = false;
        this.galleryActions.hidden = false;
        
        const card = document.createElement('div');
        card.className = 'content-card blog-card';
        
        const timestamp = new Date().toLocaleTimeString();
        
        // Extract title if present
        const titleMatch = text.match(/^#+ (.+)$/m) || text.match(/\*\*(.+?)\*\*/);
        const title = titleMatch ? titleMatch[1].substring(0, 50) : 'Blog Article';
        
        // Get preview text (first 150 chars without markdown)
        const preview = text.replace(/[#*_`]/g, '').substring(0, 150) + '...';
        
        card.innerHTML = `
            <div class="text-content-preview">
                <div class="content-header">
                    <span class="content-icon">📝</span>
                    <span class="content-title">${title}</span>
                </div>
                <div class="content-preview">${preview}</div>
                <button class="view-full-btn" data-type="blog">View Full Article</button>
            </div>
            <div class="card-info">
                <div class="card-meta">
                    <span class="card-badge blog-badge">Blog</span>
                    <span>${timestamp}</span>
                </div>
            </div>
        `;
        
        // Store the full content
        card.dataset.fullContent = text;
        card.querySelector('.view-full-btn').addEventListener('click', () => {
            this.showContentModal('Blog Article', text, 'blog');
        });
        
        this.contentGrid.insertBefore(card, this.contentGrid.firstChild);
    }
    
    addTextContentCard(text) {
        this.emptyState.hidden = true;
        this.contentGrid.hidden = false;
        this.galleryActions.hidden = false;
        
        const card = document.createElement('div');
        card.className = 'content-card text-card';
        
        const timestamp = new Date().toLocaleTimeString();
        
        // Detect content type
        let icon = '💬';
        let type = 'Response';
        const lowerText = text.toLowerCase();
        
        if (lowerText.includes('caption')) {
            icon = '✍️';
            type = 'Caption';
        } else if (lowerText.includes('hashtag')) {
            icon = '#️⃣';
            type = 'Hashtags';
        } else if (lowerText.includes('strategy')) {
            icon = '🎯';
            type = 'Strategy';
        }
        
        const preview = text.replace(/[#*_`]/g, '').substring(0, 120) + '...';
        
        card.innerHTML = `
            <div class="text-content-preview">
                <div class="content-header">
                    <span class="content-icon">${icon}</span>
                    <span class="content-title">${type}</span>
                </div>
                <div class="content-preview">${preview}</div>
            </div>
            <div class="card-info">
                <div class="card-meta">
                    <span class="card-badge">${type}</span>
                    <span>${timestamp}</span>
                </div>
            </div>
        `;
        
        this.contentGrid.insertBefore(card, this.contentGrid.firstChild);
    }
    
    showContentModal(title, content, type) {
        const modal = document.createElement('div');
        modal.className = 'content-modal';
        
        const iconHtml = {
            'blog': '📝',
            'campaign': '<svg class="modal-header-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>',
            'caption': '✍️'
        };
        
        modal.innerHTML = `
            <div class="content-modal-backdrop"></div>
            <div class="content-modal-content">
                <button class="content-modal-close">×</button>
                <div class="content-modal-header">
                    <h2>${iconHtml[type] || '📄'} ${title}</h2>
                </div>
                <div class="content-modal-body">
                    ${this.formatModalContent(content)}
                </div>
                <div class="content-modal-footer">
                    <button class="copy-content-btn">📋 Copy Content</button>
                </div>
            </div>
        `;
        
        modal.querySelector('.content-modal-backdrop').addEventListener('click', () => modal.remove());
        modal.querySelector('.content-modal-close').addEventListener('click', () => modal.remove());
        modal.querySelector('.copy-content-btn').addEventListener('click', () => {
            navigator.clipboard.writeText(content);
            modal.querySelector('.copy-content-btn').textContent = '✓ Copied!';
            setTimeout(() => {
                modal.querySelector('.copy-content-btn').textContent = '📋 Copy Content';
            }, 2000);
        });
        
        document.body.appendChild(modal);
    }
    
    formatModalContent(text) {
        // First, handle markdown tables
        const lines = text.split('\n');
        let result = [];
        let inTable = false;
        let tableRows = [];
        
        for (let i = 0; i < lines.length; i++) {
            const line = lines[i].trim();
            
            // Check if this is a table row (starts and ends with |)
            if (line.startsWith('|') && line.endsWith('|')) {
                // Skip separator rows (|---|---|)
                if (line.match(/^\|[\s\-:]+\|$/)) {
                    continue;
                }
                
                if (!inTable) {
                    inTable = true;
                    tableRows = [];
                }
                
                // Parse table cells
                const cells = line.split('|').filter(c => c.trim() !== '');
                tableRows.push(cells.map(c => c.trim()));
            } else {
                // If we were in a table, render it now
                if (inTable && tableRows.length > 0) {
                    let tableHtml = '<table class="campaign-table"><thead><tr>';
                    // First row is header
                    tableRows[0].forEach(cell => {
                        tableHtml += `<th>${cell}</th>`;
                    });
                    tableHtml += '</tr></thead><tbody>';
                    // Rest are body rows
                    for (let j = 1; j < tableRows.length; j++) {
                        tableHtml += '<tr>';
                        tableRows[j].forEach(cell => {
                            tableHtml += `<td>${cell}</td>`;
                        });
                        tableHtml += '</tr>';
                    }
                    tableHtml += '</tbody></table>';
                    result.push(tableHtml);
                    tableRows = [];
                    inTable = false;
                }
                result.push(line);
            }
        }
        
        // Handle any remaining table
        if (inTable && tableRows.length > 0) {
            let tableHtml = '<table class="campaign-table"><thead><tr>';
            tableRows[0].forEach(cell => {
                tableHtml += `<th>${cell}</th>`;
            });
            tableHtml += '</tr></thead><tbody>';
            for (let j = 1; j < tableRows.length; j++) {
                tableHtml += '<tr>';
                tableRows[j].forEach(cell => {
                    tableHtml += `<td>${cell}</td>`;
                });
                tableHtml += '</tr>';
            }
            tableHtml += '</tbody></table>';
            result.push(tableHtml);
        }
        
        // Join and apply other markdown formatting
        return result.join('\n')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/^### (.*?)$/gm, '<h3>$1</h3>')
            .replace(/^## (.*?)$/gm, '<h2>$1</h2>')
            .replace(/^# (.*?)$/gm, '<h1>$1</h1>')
            .replace(/^- (.*?)$/gm, '<li>$1</li>')
            .replace(/^\d+\. (.*?)$/gm, '<li>$1</li>')
            .replace(/---/g, '<hr>')
            .replace(/\n\n/g, '</p><p>')
            .replace(/\n/g, '<br>');
    }
    
    addCampaignCard(text) {
        // Don't add campaign summary cards to the right panel
        // Only posts with images and captions should appear there
        // The campaign info stays in the chat only
        this.currentCampaign = text;
        
        // Parse and extract any posts from the campaign
        const campaignData = this.parseCampaignStructure(text);
        
        // Only add actual posts with images to the gallery
        if (campaignData.weeks && campaignData.weeks.length > 0) {
            campaignData.weeks.forEach(week => {
                week.posts.forEach(post => {
                    if (post.image) {
                        this.addPostToGallery(post, week.number);
                    }
                });
            });
        }
    }
    
    // Add a single post (image + caption) to the gallery
    addPostToGallery(postData, weekNum = null) {
        this.emptyState.hidden = true;
        this.contentGrid.hidden = false;
        if (this.galleryActions) this.galleryActions.hidden = false;
        
        const card = this.createPostCard(postData, weekNum);
        this.contentGrid.insertBefore(card, this.contentGrid.firstChild);
    }
    
    // Parse campaign text to extract structured data
    parseCampaignStructure(text) {
        const data = {
            title: '',
            duration: '',
            postsPerWeek: '',
            totalPosts: 0,
            weeks: []
        };
        
        // Extract title
        const titleMatch = text.match(/campaign[:\s]+([^\n]+)/i) || text.match(/content plan[:\s]+([^\n]+)/i);
        if (titleMatch) data.title = titleMatch[1].trim();
        
        // Extract duration
        const durationMatch = text.match(/(\d+)\s*(?:weeks?|months?)/i);
        if (durationMatch) data.duration = durationMatch[0];
        
        // Extract posts per week
        const postsMatch = text.match(/(\d+)\s*posts?\s*(?:per|\/)\s*week/i);
        if (postsMatch) data.postsPerWeek = postsMatch[1];
        
        // Parse weeks
        const weekPattern = /(?:##?\s*)?week\s*(\d+)[:\s]*([^\n]*)?/gi;
        let weekMatch;
        let currentWeekNum = 0;
        
        while ((weekMatch = weekPattern.exec(text)) !== null) {
            const weekNum = parseInt(weekMatch[1]);
            if (weekNum > currentWeekNum) {
                currentWeekNum = weekNum;
                const weekStart = weekMatch.index;
                const nextWeekMatch = text.slice(weekStart + 10).match(/(?:##?\s*)?week\s*\d+/i);
                const weekEnd = nextWeekMatch ? weekStart + 10 + nextWeekMatch.index : text.length;
                const weekContent = text.slice(weekStart, weekEnd);
                
                const weekData = {
                    number: weekNum,
                    title: weekMatch[2]?.trim() || `Week ${weekNum}`,
                    dates: '',
                    posts: []
                };
                
                // Extract dates for this week
                const dateMatch = weekContent.match(/(?:dates?|period)[:\s]*([^\n]+)/i);
                if (dateMatch) weekData.dates = dateMatch[1].trim();
                
                // Parse posts/days within this week
                const dayPattern = /(?:day\s*(\d+)|post\s*(\d+))[:\s]*([^\n]*)/gi;
                let dayMatch;
                
                while ((dayMatch = dayPattern.exec(weekContent)) !== null) {
                    const dayNum = dayMatch[1] || dayMatch[2];
                    const dayTitle = dayMatch[3]?.trim() || '';
                    
                    // Look for image and caption near this day
                    const dayStart = dayMatch.index;
                    const nextDayMatch = weekContent.slice(dayStart + 10).match(/(?:day|post)\s*\d+/i);
                    const dayEnd = nextDayMatch ? dayStart + 10 + nextDayMatch.index : weekContent.length;
                    const dayContent = weekContent.slice(dayStart, dayEnd);
                    
                    // Extract image path
                    const imageMatch = dayContent.match(/(?:\/)?generated\/[^\s\)\"\'\`<>]+\.png/);
                    
                    // Extract caption
                    const captionMatch = dayContent.match(/caption[:\s]*\n?([\s\S]*?)(?=\n\n|hashtag|#[a-zA-Z]|$)/i);
                    
                    // Extract hashtags
                    const hashtagMatch = dayContent.match(/#[a-zA-Z][a-zA-Z0-9_]*/g);
                    
                    weekData.posts.push({
                        day: dayNum,
                        title: dayTitle,
                        image: imageMatch ? (imageMatch[0].startsWith('/') ? imageMatch[0] : '/' + imageMatch[0]) : null,
                        caption: captionMatch ? captionMatch[1].trim().replace(/\*\*/g, '') : '',
                        hashtags: hashtagMatch || []
                    });
                    
                    data.totalPosts++;
                }
                
                data.weeks.push(weekData);
            }
        }
        
        return data;
    }
    
    // Create a week section with posts
    createWeekSection(weekData) {
        const weekSection = document.createElement('div');
        weekSection.className = 'week-section';
        
        weekSection.innerHTML = `
            <div class="week-header">
                <h4>Week ${weekData.number}${weekData.title && weekData.title !== `Week ${weekData.number}` ? ': ' + weekData.title : ''}</h4>
                ${weekData.dates ? `<div class="week-dates">${weekData.dates}</div>` : ''}
            </div>
            <div class="week-posts"></div>
        `;
        
        const postsContainer = weekSection.querySelector('.week-posts');
        
        if (weekData.posts.length > 0) {
            weekData.posts.forEach(post => {
                const postCard = this.createPostCard(post, weekData.number);
                postsContainer.appendChild(postCard);
            });
        } else {
            postsContainer.innerHTML = `
                <div class="week-placeholder">
                    <p>📝 Posts for this week will appear here once generated</p>
                </div>
            `;
        }
        
        return weekSection;
    }
    
    // Create a single post card with image + caption side by side
    createPostCard(postData, weekNum) {
        const card = document.createElement('div');
        card.className = 'post-card';
        
        const hasImage = postData.image;
        const hasCaption = postData.caption && postData.caption.length > 10;
        const postLabel = postData.day ? `Post ${postData.day}` : `Post`;
        
        card.innerHTML = `
            <div class="post-header">
                <div class="post-label">
                    <span class="post-number">${postData.day || '•'}</span>
                    <div>
                        <div class="post-date">${postLabel}</div>
                        ${postData.title ? `<div class="post-theme">${postData.title}</div>` : ''}
                    </div>
                </div>
                <div class="post-badges">
                    ${hasImage ? '<span class="badge badge-image">Image</span>' : ''}
                    ${hasCaption ? '<span class="badge badge-caption">Caption</span>' : ''}
                </div>
            </div>
            <div class="post-content">
                <div class="post-image-section">
                    ${hasImage ? `
                        <div class="post-image" data-image="${postData.image}">
                            <img src="${postData.image}" alt="${postLabel}">
                            <div class="post-image-overlay">
                                <div class="overlay-actions">
                                    <button class="overlay-btn view-btn" title="View Full Size">
                                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                            <circle cx="11" cy="11" r="8"/>
                                            <path d="m21 21-4.35-4.35"/>
                                        </svg>
                                    </button>
                                    <button class="overlay-btn download-btn" title="Download">
                                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                            <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
                                            <polyline points="7 10 12 15 17 10"/>
                                            <line x1="12" y1="15" x2="12" y2="3"/>
                                        </svg>
                                    </button>
                                </div>
                            </div>
                        </div>
                    ` : `
                        <div class="post-image-placeholder">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                                <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                                <circle cx="8.5" cy="8.5" r="1.5"/>
                                <polyline points="21 15 16 10 5 21"/>
                            </svg>
                            <span>Image pending</span>
                        </div>
                    `}
                </div>
                <div class="post-caption-section">
                    <div class="caption-header">
                        <h5>Caption</h5>
                        ${hasCaption ? `
                            <button class="copy-btn" data-caption="${postData.caption.replace(/"/g, '&quot;')}">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
                                    <path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/>
                                </svg>
                                Copy
                            </button>
                        ` : ''}
                    </div>
                    <div class="caption-body">
                        ${hasCaption ? `
                            <div class="caption-text">${postData.caption.replace(/\n/g, '<br>')}</div>
                        ` : `
                            <div class="caption-placeholder">Caption will appear here once generated...</div>
                        `}
                    </div>
                    ${postData.hashtags && postData.hashtags.length > 0 ? `
                        <div class="hashtags-section">
                            <h6>Hashtags</h6>
                            <div class="hashtags-list">
                                ${postData.hashtags.slice(0, 15).map(h => `<span class="hashtag">${h}</span>`).join('')}
                            </div>
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
        
        // Add event listeners
        if (hasImage) {
            const viewBtn = card.querySelector('.view-btn');
            const downloadBtn = card.querySelector('.download-btn');
            const imageEl = card.querySelector('.post-image');
            
            imageEl?.addEventListener('click', () => this.openModal(postData.image));
            viewBtn?.addEventListener('click', (e) => {
                e.stopPropagation();
                this.openModal(postData.image);
            });
            downloadBtn?.addEventListener('click', (e) => {
                e.stopPropagation();
                this.downloadImage(postData.image, postData.image.split('/').pop());
            });
        }
        
        // Copy button
        const copyBtn = card.querySelector('.copy-btn');
        if (copyBtn) {
            copyBtn.addEventListener('click', async (e) => {
                e.stopPropagation();
                const caption = copyBtn.dataset.caption;
                const hashtags = postData.hashtags ? postData.hashtags.join(' ') : '';
                const fullText = caption + (hashtags ? '\n\n' + hashtags : '');
                
                try {
                    await navigator.clipboard.writeText(fullText);
                    copyBtn.innerHTML = '✓ Copied!';
                    setTimeout(() => {
                        copyBtn.innerHTML = `
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
                                <path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/>
                            </svg>
                            Copy
                        `;
                    }, 2000);
                } catch (err) {}
            });
        }
        
        // Hashtag click to copy
        card.querySelectorAll('.hashtag').forEach(tag => {
            tag.addEventListener('click', async () => {
                try {
                    await navigator.clipboard.writeText(tag.textContent);
                    tag.style.background = 'var(--primary)';
                    tag.style.color = 'white';
                    setTimeout(() => {
                        tag.style.background = '';
                        tag.style.color = '';
                    }, 500);
                } catch (err) {}
            });
        });
        
        return card;
    }
    
    showTypingIndicator() {
        const id = 'typing-' + Date.now();
        const indicator = document.createElement('div');
        indicator.className = 'message assistant';
        indicator.id = id;
        indicator.innerHTML = `
            <div class="message-avatar">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"/>
                    <path d="M8 14s1.5 2 4 2 4-2 4-2"/>
                    <line x1="9" y1="9" x2="9.01" y2="9"/>
                    <line x1="15" y1="9" x2="15.01" y2="9"/>
                </svg>
            </div>
            <div class="message-content">
                <div class="typing-indicator"><span></span><span></span><span></span></div>
            </div>
        `;
        this.chatMessages.appendChild(indicator);
        this.scrollToBottom();
        return id;
    }
    
    removeTypingIndicator(id) {
        document.getElementById(id)?.remove();
    }
    
    scrollToBottom() {
        this.chatContainer.scrollTop = this.chatContainer.scrollHeight;
    }
    
    parseAssistantResponse(text) {
        console.log('🔍 Parsing assistant response for images...');
        console.log('📝 Response text:', text.substring(0, 500));
        
        // Parse image-caption pairs from the response
        const imageCaptionPairs = this.extractImageCaptionPairs(text);
        
        console.log('📋 Image-caption pairs found:', imageCaptionPairs.length);
        
        if (imageCaptionPairs.length > 0) {
            // Add images with their associated captions
            imageCaptionPairs.forEach(pair => {
                console.log('🖼️ Pair:', pair.image, 'Caption:', pair.caption?.substring(0, 50));
                if (!this.generatedImages.includes(pair.image)) {
                    // New image - add to gallery
                    this.generatedImages.push(pair.image);
                    this.addImageToGalleryWithCaption(pair.image, pair.caption, pair.hashtags);
                    this.saveImagesToStorage();
                } else if (pair.caption || (pair.hashtags && pair.hashtags.length > 0)) {
                    // Image already exists but now we have caption/hashtags (carousel complete scenario)
                    // Update the existing gallery card with caption/hashtags
                    console.log('🔄 Updating existing image with caption/hashtags:', pair.image);
                    this.updateGalleryCardWithCaption(pair.image, pair.caption, pair.hashtags);
                    this.saveImagesToStorage();
                }
            });
        } else {
            // Fallback: Check for generated images without caption association
            // Multiple patterns to catch different formats
            const patterns = [
                /\*\*(?:📸\s*)?Image:\*\*\s*(\/generated\/[^\s\n]+\.png)/gi,  // **📸 Image:** or **Image:** /generated/xxx.png
                /📸\s*Image:\s*(\/generated\/[^\s\n]+\.png)/gi,  // 📸 Image: /generated/xxx.png
                /Image:\s*(\/generated\/[^\s\n]+\.png)/gi,  // Image: /generated/xxx.png
                /\[📷[^\]]*\]\((\/generated\/[^\)]+\.png)\)/gi,  // Markdown link: [📷 View Image](/generated/xxx.png)
                /\[[^\]]*\]\((\/generated\/[^\)]+\.png)\)/gi,    // Any markdown link to generated image
                /\/generated\/post_[a-zA-Z0-9_]+\.png/g,  // /generated/post_xxx.png (specific)
                /\/generated\/[a-zA-Z0-9_-]+\.png/g,  // /generated/xxx.png (general)
                /generated\/[a-zA-Z0-9_-]+\.png/g,    // Without leading slash
                /\(\/generated\/[^)]+\.png\)/g,       // Markdown image: ![](url)
            ];
            
            const allMatches = new Set();
            patterns.forEach(pattern => {
                const matches = text.match(pattern);
                if (matches) {
                    matches.forEach(match => {
                        // Clean up the match - remove markdown syntax and **Image:** prefix
                        let cleanPath = match.replace(/\*\*Image:\*\*\s*/gi, '').replace(/[\(\)]/g, '').trim();
                        if (!cleanPath.startsWith('/')) {
                            cleanPath = '/' + cleanPath;
                        }
                        // Validate it looks like an image path
                        if (cleanPath.includes('/generated/') && cleanPath.endsWith('.png')) {
                            allMatches.add(cleanPath);
                        }
                    });
                }
            });
            
            console.log('🖼️ Found images (fallback):', Array.from(allMatches));
            allMatches.forEach(imgPath => {
                if (!this.generatedImages.includes(imgPath)) {
                    console.log('➕ Adding image to gallery:', imgPath);
                    this.generatedImages.push(imgPath);

                    // Try to extract caption and hashtags from response text
                    // Search in full text since caption may appear before or after the image path
                    let caption = '';
                    let hashtags = [];

                    // Look for caption section anywhere in the response
                    const captionPatterns = [
                        /(?:\*\*)?(?:📝\s*)?Caption(?:\*\*)?:?\s*\n?([\s\S]*?)(?=#️⃣|Hashtags:|---|\n\n\*\*What|\n\nOptions:|$)/i,
                        /(?:📝\s*)?Caption:?\s*\n([\s\S]*?)(?=\n\n#️⃣|\n\n.*Hashtags|\n---|\n\n\*\*What|\n\nOptions:|$)/i,
                    ];
                    for (const cp of captionPatterns) {
                        const cm = text.match(cp);
                        if (cm && cm[1].trim().length > 10) {
                            caption = cm[1].trim().replace(/\*\*/g, '').substring(0, 800);
                            break;
                        }
                    }

                    // Look for hashtags anywhere in the response
                    const hashtagMatch = text.match(/#[a-zA-Z][a-zA-Z0-9_]*/g);
                    hashtags = hashtagMatch ? hashtagMatch.slice(0, 25) : [];

                    if (caption || hashtags.length > 0) {
                        console.log('📝 Found caption/hashtags for fallback image');
                        this.addImageToGalleryWithCaption(imgPath, caption, hashtags);
                    } else {
                        this.addImageToGallery(imgPath);
                    }
                    this.saveImagesToStorage();
                }
            });
        }
        
        // Check for generated videos (animated content)
        const videoPattern = /(?:\/)?generated\/[^\s\)\"\'\`<>]+\.(mp4|webm|mov)/gi;
        const videoMatches = text.match(videoPattern);

        if (videoMatches) {
            const videos = videoMatches.map(path => path.startsWith('/') ? path : '/' + path);
            videos.forEach(videoPath => {
                if (!this.generatedImages.includes(videoPath)) {
                    this.generatedImages.push(videoPath);

                    // Try to get caption/hashtags from the most recent image post
                    // (the video is an animation of a previously generated image)
                    let videoCaption = '';
                    let videoHashtags = [];

                    // Check if we have metadata from a recent image
                    const lastImage = this.generatedImages.filter(p => /\.(png|jpg|jpeg)$/i.test(p)).pop();
                    if (lastImage && this.generatedImagesMeta && this.generatedImagesMeta[lastImage]) {
                        const meta = this.generatedImagesMeta[lastImage];
                        videoCaption = meta.caption || '';
                        videoHashtags = meta.hashtags || [];
                    }

                    if (videoCaption || videoHashtags.length > 0) {
                        this.addVideoToGalleryWithCaption(videoPath, videoCaption, videoHashtags);
                    } else {
                        this.addImageToGallery(videoPath);
                    }
                    this.saveImagesToStorage();
                }
            });
        }
        
        // Check for hashtags (for general display)
        const hashtagPattern = /#[a-zA-Z0-9_]+/g;
        const hashtags = text.match(hashtagPattern);
        if (hashtags && hashtags.length > 5) {
            this.displayHashtags(hashtags);
        }
        
        // Add click handlers for image links
        setTimeout(() => {
            document.querySelectorAll('.image-link').forEach(link => {
                link.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.openModal(link.dataset.image);
                });
            });
        }, 100);
    }
    
    // Extract image-caption pairs from response text
    extractImageCaptionPairs(text) {
        const pairs = [];
        let match;

        // Pattern 1: Campaign post format - "✅ Post X of Y Created!" followed by image/caption/hashtags
        // This handles the campaign agent output format
        const campaignPostPattern = /(?:✅\s*)?Post\s*\d+\s*(?:of\s*\d+)?\s*Created!?\s*\n+(?:📷\s*)?(?:\*\*)?Image(?:\*\*)?:?\s*[^\n]*?(\/generated\/[^\s\)\"\'\`<>\n]+\.png)[\s\S]*?(?:Caption|📝\s*Caption):?\s*\n([\s\S]*?)(?=Hashtags:|#️⃣|Full Post|---|\n\n✅|\n\n📷|$)/gi;

        while ((match = campaignPostPattern.exec(text)) !== null) {
            const imagePath = match[1].startsWith('/') ? match[1] : '/' + match[1];
            let captionText = match[2].trim();

            // Clean up caption
            captionText = captionText.replace(/\*\*/g, '').replace(/^\s*\n/gm, '').trim();

            // Extract hashtags after caption section
            const afterCaption = text.slice(match.index + match[0].length, match.index + match[0].length + 1500);
            const hashtagMatch = afterCaption.match(/#[a-zA-Z][a-zA-Z0-9_]*/g);

            if (!pairs.find(p => p.image === imagePath)) {
                pairs.push({
                    image: imagePath,
                    caption: captionText.substring(0, 800),
                    hashtags: hashtagMatch ? hashtagMatch.slice(0, 25) : []
                });
            }
        }

        // Pattern 1.5: Carousel completion format - table with images + shared caption/hashtags at end
        // Handles the "🎊 Carousel Complete!" format with table of slides
        if (pairs.length === 0) {
            // First check if this looks like a carousel completion message
            const isCarouselComplete = text.includes('Carousel Complete') || text.includes('carousel complete') ||
                                       (text.includes('Slide') && text.includes('Headline') && text.includes('Image'));

            if (isCarouselComplete) {
                // Extract the shared caption for all carousel slides
                const captionMatch = text.match(/(?:📝\s*)?(?:\*\*)?Caption(?:\*\*)?:?\s*\n?([\s\S]*?)(?=(?:#️⃣|📌)\s*(?:\*\*)?Hashtags|\n---|\n\n\*\*What|$)/i);
                const sharedCaption = captionMatch ? captionMatch[1].trim().replace(/\*\*/g, '').substring(0, 800) : '';

                // Extract hashtags
                const hashtagMatch = text.match(/#[a-zA-Z][a-zA-Z0-9_]*/g);
                const sharedHashtags = hashtagMatch ? hashtagMatch.slice(0, 25) : [];

                console.log('🎠 Carousel complete detected, shared caption:', sharedCaption.substring(0, 50));
                console.log('🎠 Shared hashtags:', sharedHashtags.length);

                // Extract all image paths from the carousel (from table or View Image links)
                const imagePatterns = [
                    /\[📷[^\]]*\]\((\/generated\/[^\)]+\.png)\)/gi,  // [📷 View Image](/generated/xxx.png)
                    /\|\s*(\/generated\/[^\|\s\n]+\.png)\s*\|/gi,  // Plain path in table cell: | /generated/xxx.png |
                    /\|\s*\[?📷?[^\]]*\]?\(?(\/generated\/[^\)\|\s]+\.png)\)?/gi,  // Table cell with brackets
                    /(?:📸\s*)?(?:\*\*)?Image(?:\*\*)?:?\s*(?:\[📷[^\]]*\]\()?(\/generated\/[^\s\)\n]+\.png)\)?/gi,  // 📸 Image: format
                    /(\/generated\/post_[a-zA-Z0-9_]+\.png)/gi,  // Direct path: /generated/post_xxx.png
                ];

                const foundImages = new Set();
                imagePatterns.forEach((pattern, idx) => {
                    let imgMatch;
                    while ((imgMatch = pattern.exec(text)) !== null) {
                        let imgPath = imgMatch[1];
                        if (imgPath && !imgPath.startsWith('/')) imgPath = '/' + imgPath;
                        if (imgPath && imgPath.includes('/generated/')) {
                            foundImages.add(imgPath);
                            console.log(`🎠 Pattern ${idx} matched:`, imgPath);
                        }
                    }
                });
                console.log('🎠 Total unique carousel images found:', foundImages.size);

                // Add each carousel image with the shared caption/hashtags
                foundImages.forEach(imagePath => {
                    if (!pairs.find(p => p.image === imagePath)) {
                        pairs.push({
                            image: imagePath,
                            caption: sharedCaption,
                            hashtags: sharedHashtags
                        });
                        console.log('🎠 Added carousel image with shared caption:', imagePath);
                    }
                });
            }
        }

        // Pattern 1.6: Individual carousel slide format - "🎉 Slide X of Y:" (without shared caption)
        // For slides shown during generation (before carousel is complete)
        if (pairs.length === 0) {
            const carouselSlidePattern = /(?:🎉\s*)?Slide\s*(\d+)\s*of\s*(\d+):?\s*[^\n]*\n+(?:📸\s*)?(?:\*\*)?Image(?:\*\*)?:?\s*(?:\[📷[^\]]*\]\()?([^\s\)\"\'\`<>\n]+\.png)\)?/gi;

            while ((match = carouselSlidePattern.exec(text)) !== null) {
                let imagePath = match[3];
                if (!imagePath.startsWith('/')) {
                    imagePath = '/' + imagePath;
                }

                // For individual slides, look for description after the image
                const slideSection = text.slice(match.index, match.index + 500);
                const descMatch = slideSection.match(/This slide[^\n]*/i);
                const description = descMatch ? descMatch[0] : '';

                if (!pairs.find(p => p.image === imagePath)) {
                    pairs.push({
                        image: imagePath,
                        caption: description,
                        hashtags: []
                    });
                    console.log('🎠 Found individual carousel slide:', match[1], 'of', match[2], imagePath);
                }
            }
        }

        // Pattern 2: Structured format with **📸 Image:** and **📝 Caption:** (flexible matching)
        if (pairs.length === 0) {
            // More flexible pattern that handles variations like:
            // **📸 Image:** /generated/xxx.png
            // **📝 Caption:**
            // caption text...
            const structuredPattern = /\*\*(?:📸\s*)?Image:?\*\*\s*(\/generated\/[^\s\n]+\.png)[\s\S]*?\*\*(?:📝\s*)?Caption:?\*\*\s*\n?([\s\S]*?)(?=\*\*(?:#️⃣|Hashtags)|#️⃣\s*(?:\*\*)?Hashtags|\n---|\n\*\*What|\n\nOptions:)/gi;

            while ((match = structuredPattern.exec(text)) !== null) {
                const imagePath = match[1].startsWith('/') ? match[1] : '/' + match[1];
                let captionText = match[2].trim();
                captionText = captionText.replace(/\*\*/g, '').replace(/^\s*\n/gm, '').trim();

                const afterCaption = text.slice(match.index + match[0].length, match.index + match[0].length + 1000);
                const hashtagMatch = afterCaption.match(/#[a-zA-Z][a-zA-Z0-9_]*/g);

                if (!pairs.find(p => p.image === imagePath)) {
                    pairs.push({
                        image: imagePath,
                        caption: captionText.substring(0, 800),
                        hashtags: hashtagMatch ? hashtagMatch.slice(0, 25) : []
                    });
                }
            }
        }

        // Pattern 3: Single post format - "Here's your single post" or similar
        if (pairs.length === 0) {
            const singlePostPattern = /(?:Here's your|Here is your|Your)[^\n]*?(?:post|image)[^\n]*\n+(?:📷\s*)?(?:\*\*)?Image(?:\*\*)?:?\s*[^\n]*?(\/generated\/[^\s\)\"\'\`<>\n]+\.png)[\s\S]*?(?:Caption|📝\s*Caption):?\s*\n([\s\S]*?)(?=Hashtags:|#️⃣|Full Post|---|\n\n\*\*What|$)/gi;

            while ((match = singlePostPattern.exec(text)) !== null) {
                const imagePath = match[1].startsWith('/') ? match[1] : '/' + match[1];
                let captionText = match[2].trim();
                captionText = captionText.replace(/\*\*/g, '').replace(/^\s*\n/gm, '').trim();

                const afterCaption = text.slice(match.index + match[0].length, match.index + match[0].length + 1000);
                const hashtagMatch = afterCaption.match(/#[a-zA-Z][a-zA-Z0-9_]*/g);

                if (!pairs.find(p => p.image === imagePath)) {
                    pairs.push({
                        image: imagePath,
                        caption: captionText.substring(0, 800),
                        hashtags: hashtagMatch ? hashtagMatch.slice(0, 25) : []
                    });
                }
            }
        }

        // Pattern 4: Generic image path with nearby Caption: section
        if (pairs.length === 0) {
            const genericPattern = /(\/generated\/[^\s\)\"\'\`<>\n]+\.png)[\s\S]{0,200}?(?:Caption|📝):?\s*\n([\s\S]*?)(?=Hashtags:|#️⃣|Full Post|---|\n\n\n|$)/gi;

            while ((match = genericPattern.exec(text)) !== null) {
                const imagePath = match[1].startsWith('/') ? match[1] : '/' + match[1];
                let captionText = match[2].trim();
                captionText = captionText.replace(/\*\*/g, '').replace(/^\s*\n/gm, '').trim();

                const afterCaption = text.slice(match.index + match[0].length, match.index + match[0].length + 500);
                const hashtagMatch = afterCaption.match(/#[a-zA-Z][a-zA-Z0-9_]*/g);

                if (!pairs.find(p => p.image === imagePath)) {
                    pairs.push({
                        image: imagePath,
                        caption: captionText.substring(0, 800),
                        hashtags: hashtagMatch ? hashtagMatch.slice(0, 25) : []
                    });
                }
            }
        }

        console.log('📋 Extracted image-caption pairs:', pairs);
        return pairs;
    }
    
    // Add image to gallery WITH associated caption
    addImageToGalleryWithCaption(imagePath, caption, hashtags) {
        // Sanitize image path - remove any markdown/prefix artifacts
        imagePath = this.sanitizeImagePath(imagePath);
        if (!imagePath) return;

        // Save metadata for this image (for persistence)
        if (!this.generatedImagesMeta) this.generatedImagesMeta = {};
        this.generatedImagesMeta[imagePath] = {
            caption: caption || '',
            hashtags: hashtags || []
        };

        this.emptyState.hidden = true;
        this.contentGrid.hidden = false;
        this.galleryActions.hidden = false;

        const card = document.createElement('div');
        card.className = 'content-card image-with-caption-card';

        const filename = imagePath.split('/').pop();
        const timestamp = new Date().toLocaleTimeString();
        const captionPreview = caption ? caption.substring(0, 150) + (caption.length > 150 ? '...' : '') : '';
        const hashtagsStr = hashtags && hashtags.length > 0 ? hashtags.join(' ') : '';

        card.innerHTML = `
            <div class="card-image" data-image="${imagePath}">
                <img src="${imagePath}" alt="Generated content">
                <div class="card-overlay">
                    <div class="overlay-actions">
                        <button class="overlay-btn view-btn" title="View">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <circle cx="11" cy="11" r="8"/>
                                <path d="m21 21-4.35-4.35"/>
                            </svg>
                        </button>
                        <button class="overlay-btn download-btn" title="Download">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
                                <polyline points="7 10 12 15 17 10"/>
                                <line x1="12" y1="15" x2="12" y2="3"/>
                            </svg>
                        </button>
                    </div>
                </div>
            </div>
            <div class="card-caption-section ${!caption && !hashtagsStr ? 'hidden' : ''}">
                ${caption ? `
                <div class="caption-header">
                    <span class="caption-label">📝 Caption</span>
                    <button class="copy-btn copy-caption-btn" title="Copy caption">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14">
                            <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                            <path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"></path>
                        </svg>
                        Copy
                    </button>
                </div>
                <div class="card-caption-text">${captionPreview}</div>
                ${caption.length > 150 ? `
                <button class="expand-caption-btn" data-expanded="false">
                    View Full Caption ▼
                </button>
                <div class="card-caption-full">${caption.replace(/\n/g, '<br>')}</div>
                ` : ''}
                ` : ''}
                ${hashtagsStr ? `
                <div class="hashtags-section">
                    <div class="hashtags-header">
                        <span class="hashtags-label">#️⃣ Hashtags</span>
                        <button class="copy-btn copy-hashtags-btn" title="Copy hashtags">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14">
                                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                                <path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"></path>
                            </svg>
                            Copy
                        </button>
                    </div>
                    <div class="card-hashtags-text">${hashtagsStr}</div>
                </div>
                ` : ''}
                ${caption && hashtagsStr ? `
                <div class="copy-all-section">
                    <button class="copy-btn copy-all-btn" title="Copy caption + hashtags">
                        📋 Copy Full Post
                    </button>
                </div>
                ` : ''}
            </div>
            <div class="card-info">
                <div class="card-meta">
                    <span class="card-badge">New</span>
                    <span>${timestamp}</span>
                </div>
            </div>
        `;
        
        // Event handlers
        card.querySelector('.card-image').addEventListener('click', () => this.openModal(imagePath));
        card.querySelector('.view-btn').addEventListener('click', (e) => {
            e.stopPropagation();
            this.openModal(imagePath);
        });
        card.querySelector('.download-btn').addEventListener('click', (e) => {
            e.stopPropagation();
            this.downloadImage(imagePath, filename);
        });

        // Expand caption handler
        const expandBtn = card.querySelector('.expand-caption-btn');
        if (expandBtn) {
            expandBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                const fullCaption = card.querySelector('.card-caption-full');
                const isExpanded = expandBtn.dataset.expanded === 'true';

                if (isExpanded) {
                    fullCaption.classList.remove('expanded');
                    expandBtn.textContent = 'View Full Caption ▼';
                    expandBtn.dataset.expanded = 'false';
                } else {
                    fullCaption.classList.add('expanded');
                    expandBtn.textContent = 'Hide Caption ▲';
                    expandBtn.dataset.expanded = 'true';
                }
            });
        }

        // Copy caption handler
        const copyCaptionBtn = card.querySelector('.copy-caption-btn');
        if (copyCaptionBtn && caption) {
            copyCaptionBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.copyToClipboard(caption, copyCaptionBtn);
            });
        }

        // Copy hashtags handler
        const copyHashtagsBtn = card.querySelector('.copy-hashtags-btn');
        if (copyHashtagsBtn && hashtagsStr) {
            copyHashtagsBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.copyToClipboard(hashtagsStr, copyHashtagsBtn);
            });
        }

        // Copy full post handler (caption + hashtags)
        const copyAllBtn = card.querySelector('.copy-all-btn');
        if (copyAllBtn && caption && hashtagsStr) {
            copyAllBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                const fullPost = `${caption}\n\n.\n.\n.\n\n${hashtagsStr}`;
                this.copyToClipboard(fullPost, copyAllBtn);
            });
        }

        // Store the full caption and hashtags on the card for copying
        card.dataset.caption = caption || '';
        card.dataset.hashtags = hashtagsStr;

        this.contentGrid.insertBefore(card, this.contentGrid.firstChild);
    }

    // Update an existing gallery card with caption and hashtags (for carousel completion)
    updateGalleryCardWithCaption(imagePath, caption, hashtags) {
        imagePath = this.sanitizeImagePath(imagePath);
        if (!imagePath) return;

        // Update metadata
        if (!this.generatedImagesMeta) this.generatedImagesMeta = {};
        this.generatedImagesMeta[imagePath] = {
            caption: caption || '',
            hashtags: hashtags || []
        };

        // Find the existing card by image path
        const existingCard = this.contentGrid.querySelector(`.card-image[data-image="${imagePath}"]`)?.closest('.content-card');

        if (existingCard) {
            console.log('🔄 Found existing card, updating with caption/hashtags');

            const hashtagsStr = hashtags && hashtags.length > 0 ? hashtags.join(' ') : '';
            const captionPreview = caption ? caption.substring(0, 150) + (caption.length > 150 ? '...' : '') : '';

            // Check if caption section already exists
            let captionSection = existingCard.querySelector('.card-caption-section');

            if (!captionSection) {
                // Create new caption section
                captionSection = document.createElement('div');
                captionSection.className = 'card-caption-section';

                // Insert before the card-info section
                const cardInfo = existingCard.querySelector('.card-info');
                if (cardInfo) {
                    existingCard.insertBefore(captionSection, cardInfo);
                } else {
                    existingCard.appendChild(captionSection);
                }
            }

            // Update caption section content
            captionSection.classList.remove('hidden');
            captionSection.innerHTML = `
                ${caption ? `
                <div class="caption-header">
                    <span class="caption-label">📝 Caption</span>
                    <button class="copy-btn copy-caption-btn" title="Copy caption">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14">
                            <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                            <path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"></path>
                        </svg>
                        Copy
                    </button>
                </div>
                <div class="card-caption-text">${captionPreview}</div>
                ${caption.length > 150 ? `
                <button class="expand-caption-btn" data-expanded="false">
                    View Full Caption ▼
                </button>
                <div class="card-caption-full">${caption.replace(/\n/g, '<br>')}</div>
                ` : ''}
                ` : ''}
                ${hashtagsStr ? `
                <div class="hashtags-section">
                    <div class="hashtags-header">
                        <span class="hashtags-label">#️⃣ Hashtags</span>
                        <button class="copy-btn copy-hashtags-btn" title="Copy hashtags">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14">
                                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                                <path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"></path>
                            </svg>
                            Copy
                        </button>
                    </div>
                    <div class="card-hashtags-text">${hashtagsStr}</div>
                </div>
                ` : ''}
                ${caption && hashtagsStr ? `
                <div class="copy-all-section">
                    <button class="copy-btn copy-all-btn" title="Copy caption + hashtags">
                        📋 Copy Full Post
                    </button>
                </div>
                ` : ''}
            `;

            // Update data attributes
            existingCard.dataset.caption = caption || '';
            existingCard.dataset.hashtags = hashtagsStr;

            // Re-attach event handlers for copy buttons
            this.attachCaptionCopyHandlers(existingCard, caption, hashtagsStr);

            console.log('✅ Updated card with caption/hashtags');
        } else {
            console.log('⚠️ Could not find existing card for:', imagePath);
        }
    }

    // Attach copy handlers to caption section buttons
    attachCaptionCopyHandlers(card, caption, hashtagsStr) {
        const copyCaptionBtn = card.querySelector('.copy-caption-btn');
        if (copyCaptionBtn) {
            copyCaptionBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                navigator.clipboard.writeText(caption || '');
                this.showToast('Caption copied!');
            });
        }

        const copyHashtagsBtn = card.querySelector('.copy-hashtags-btn');
        if (copyHashtagsBtn) {
            copyHashtagsBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                navigator.clipboard.writeText(hashtagsStr || '');
                this.showToast('Hashtags copied!');
            });
        }

        const copyAllBtn = card.querySelector('.copy-all-btn');
        if (copyAllBtn) {
            copyAllBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                const fullPost = `${caption || ''}\n\n${hashtagsStr || ''}`.trim();
                navigator.clipboard.writeText(fullPost);
                this.showToast('Full post copied!');
            });
        }

        const expandBtn = card.querySelector('.expand-caption-btn');
        if (expandBtn) {
            expandBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                const fullCaption = card.querySelector('.card-caption-full');
                const isExpanded = expandBtn.dataset.expanded === 'true';

                if (isExpanded) {
                    fullCaption.classList.remove('expanded');
                    expandBtn.textContent = 'View Full Caption ▼';
                    expandBtn.dataset.expanded = 'false';
                } else {
                    fullCaption.classList.add('expanded');
                    expandBtn.textContent = 'Hide Full Caption ▲';
                    expandBtn.dataset.expanded = 'true';
                }
            });
        }
    }

    addImageToGallery(imagePath) {
        // Sanitize image path - remove any markdown/prefix artifacts
        imagePath = this.sanitizeImagePath(imagePath);
        if (!imagePath) return;

        this.emptyState.hidden = true;
        this.contentGrid.hidden = false;
        this.galleryActions.hidden = false;

        const card = document.createElement('div');
        const filename = imagePath.split('/').pop();
        const timestamp = new Date().toLocaleTimeString();
        
        // Check if it's a video file
        const isVideo = /\.(mp4|webm|mov|avi)$/i.test(imagePath);
        
        if (isVideo) {
            card.className = 'content-card video-card';
            card.innerHTML = `
                <div class="card-video" data-video="${imagePath}">
                    <video src="${imagePath}" loop muted playsinline>
                        Your browser does not support the video tag.
                    </video>
                    <div class="video-badge">
                        <svg viewBox="0 0 24 24" fill="currentColor" width="12" height="12">
                            <polygon points="5 3 19 12 5 21 5 3"/>
                        </svg>
                        Video
                    </div>
                    <div class="card-overlay">
                        <div class="overlay-actions">
                            <button class="overlay-btn download-btn" title="Download">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
                                    <polyline points="7 10 12 15 17 10"/>
                                    <line x1="12" y1="15" x2="12" y2="3"/>
                                </svg>
                            </button>
                        </div>
                    </div>
                </div>
                <div class="video-controls">
                    <button class="video-play-btn" title="Play/Pause">
                        <svg class="play-icon" viewBox="0 0 24 24" fill="currentColor" width="16" height="16">
                            <polygon points="5 3 19 12 5 21 5 3"/>
                        </svg>
                        <svg class="pause-icon" viewBox="0 0 24 24" fill="currentColor" width="16" height="16" style="display:none">
                            <rect x="6" y="4" width="4" height="16"/>
                            <rect x="14" y="4" width="4" height="16"/>
                        </svg>
                        <span class="video-play-label">Play</span>
                    </button>
                    <button class="video-sound-btn" title="Unmute">
                        <svg class="muted-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
                            <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/>
                            <line x1="23" y1="9" x2="17" y2="15"/>
                            <line x1="17" y1="9" x2="23" y2="15"/>
                        </svg>
                        <svg class="unmuted-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16" style="display:none">
                            <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/>
                            <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"/>
                        </svg>
                    </button>
                </div>
                <div class="card-info">
                    <div class="card-meta">
                        <span class="card-badge video-badge-text">🎬 Animated</span>
                        <span>${timestamp}</span>
                    </div>
                </div>
            `;

            const video = card.querySelector('video');
            const playBtn = card.querySelector('.video-play-btn');
            const playLabel = card.querySelector('.video-play-label');
            const playIcon = card.querySelector('.play-icon');
            const pauseIcon = card.querySelector('.pause-icon');
            const soundBtn = card.querySelector('.video-sound-btn');
            const mutedIcon = card.querySelector('.muted-icon');
            const unmutedIcon = card.querySelector('.unmuted-icon');

            // Play/Pause button
            playBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                if (video.paused) {
                    video.play();
                    playIcon.style.display = 'none';
                    pauseIcon.style.display = 'inline';
                    playLabel.textContent = 'Pause';
                } else {
                    video.pause();
                    playIcon.style.display = 'inline';
                    pauseIcon.style.display = 'none';
                    playLabel.textContent = 'Play';
                }
            });

            // Sound toggle button
            soundBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                video.muted = !video.muted;
                mutedIcon.style.display = video.muted ? 'inline' : 'none';
                unmutedIcon.style.display = video.muted ? 'none' : 'inline';
                soundBtn.title = video.muted ? 'Unmute' : 'Mute';
            });

            card.querySelector('.download-btn').addEventListener('click', (e) => {
                e.stopPropagation();
                this.downloadImage(imagePath, filename);
            });

            // Click video area to open in modal
            card.querySelector('.card-video').addEventListener('click', () => this.openVideoModal(imagePath));
            
        } else {
            // Regular image handling
            card.className = 'content-card';
            card.innerHTML = `
                <div class="card-image" data-image="${imagePath}">
                    <img src="${imagePath}" alt="Generated content">
                    <div class="card-overlay">
                        <div class="overlay-actions">
                            <button class="overlay-btn view-btn" title="View">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <circle cx="11" cy="11" r="8"/>
                                    <path d="m21 21-4.35-4.35"/>
                                </svg>
                            </button>
                            <button class="overlay-btn download-btn" title="Download">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
                                    <polyline points="7 10 12 15 17 10"/>
                                    <line x1="12" y1="15" x2="12" y2="3"/>
                                </svg>
                            </button>
                        </div>
                    </div>
                </div>
                <div class="card-info">
                    <div class="card-meta">
                        <span class="card-badge">New</span>
                        <span>${timestamp}</span>
                    </div>
                </div>
            `;
            
            card.querySelector('.card-image').addEventListener('click', () => this.openModal(imagePath));
            card.querySelector('.view-btn').addEventListener('click', (e) => {
                e.stopPropagation();
                this.openModal(imagePath);
            });
            card.querySelector('.download-btn').addEventListener('click', (e) => {
                e.stopPropagation();
                this.downloadImage(imagePath, filename);
            });
        }
        
        this.contentGrid.insertBefore(card, this.contentGrid.firstChild);
    }

    // Add video to gallery WITH associated caption/hashtags from the original image post
    addVideoToGalleryWithCaption(videoPath, caption, hashtags) {
        videoPath = this.sanitizeImagePath(videoPath);
        if (!videoPath) return;

        // Save metadata for this video
        if (!this.generatedImagesMeta) this.generatedImagesMeta = {};
        this.generatedImagesMeta[videoPath] = {
            caption: caption || '',
            hashtags: hashtags || []
        };

        this.emptyState.hidden = true;
        this.contentGrid.hidden = false;
        this.galleryActions.hidden = false;

        const card = document.createElement('div');
        card.className = 'content-card video-card';
        const filename = videoPath.split('/').pop();
        const timestamp = new Date().toLocaleTimeString();
        const captionPreview = caption ? caption.substring(0, 150) + (caption.length > 150 ? '...' : '') : '';
        const hashtagsStr = hashtags && hashtags.length > 0 ? hashtags.join(' ') : '';

        card.innerHTML = `
            <div class="card-video" data-video="${videoPath}">
                <video src="${videoPath}" loop muted playsinline>
                    Your browser does not support the video tag.
                </video>
                <div class="video-badge">
                    <svg viewBox="0 0 24 24" fill="currentColor" width="12" height="12">
                        <polygon points="5 3 19 12 5 21 5 3"/>
                    </svg>
                    Video
                </div>
                <div class="card-overlay">
                    <div class="overlay-actions">
                        <button class="overlay-btn download-btn" title="Download">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
                                <polyline points="7 10 12 15 17 10"/>
                                <line x1="12" y1="15" x2="12" y2="3"/>
                            </svg>
                        </button>
                    </div>
                </div>
            </div>
            <div class="video-controls">
                <button class="video-play-btn" title="Play/Pause">
                    <svg class="play-icon" viewBox="0 0 24 24" fill="currentColor" width="16" height="16">
                        <polygon points="5 3 19 12 5 21 5 3"/>
                    </svg>
                    <svg class="pause-icon" viewBox="0 0 24 24" fill="currentColor" width="16" height="16" style="display:none">
                        <rect x="6" y="4" width="4" height="16"/>
                        <rect x="14" y="4" width="4" height="16"/>
                    </svg>
                    <span class="video-play-label">Play</span>
                </button>
                <button class="video-sound-btn" title="Unmute">
                    <svg class="muted-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
                        <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/>
                        <line x1="23" y1="9" x2="17" y2="15"/>
                        <line x1="17" y1="9" x2="23" y2="15"/>
                    </svg>
                    <svg class="unmuted-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16" style="display:none">
                        <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/>
                        <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"/>
                    </svg>
                </button>
            </div>
            <div class="card-caption-section ${!caption && !hashtagsStr ? 'hidden' : ''}">
                ${caption ? `
                <div class="caption-header">
                    <span class="caption-label">📝 Caption</span>
                    <button class="copy-btn copy-caption-btn" title="Copy caption">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14">
                            <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                            <path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"></path>
                        </svg>
                        Copy
                    </button>
                </div>
                <div class="card-caption-text">${captionPreview}</div>
                ${caption.length > 150 ? `
                <button class="expand-caption-btn" data-expanded="false">
                    View Full Caption ▼
                </button>
                <div class="card-caption-full">${caption.replace(/\n/g, '<br>')}</div>
                ` : ''}
                ` : ''}
                ${hashtagsStr ? `
                <div class="hashtags-section">
                    <div class="hashtags-header">
                        <span class="hashtags-label">#️⃣ Hashtags</span>
                        <button class="copy-btn copy-hashtags-btn" title="Copy hashtags">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14">
                                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                                <path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"></path>
                            </svg>
                            Copy
                        </button>
                    </div>
                    <div class="card-hashtags-text">${hashtagsStr}</div>
                </div>
                ` : ''}
                ${caption && hashtagsStr ? `
                <div class="copy-all-section">
                    <button class="copy-btn copy-all-btn" title="Copy caption + hashtags">
                        📋 Copy Full Post
                    </button>
                </div>
                ` : ''}
            </div>
            <div class="card-info">
                <div class="card-meta">
                    <span class="card-badge video-badge-text">🎬 Animated</span>
                    <span>${timestamp}</span>
                </div>
            </div>
        `;

        // Video controls
        const video = card.querySelector('video');
        const playBtn = card.querySelector('.video-play-btn');
        const playLabel = card.querySelector('.video-play-label');
        const playIcon = card.querySelector('.play-icon');
        const pauseIcon = card.querySelector('.pause-icon');
        const soundBtn = card.querySelector('.video-sound-btn');
        const mutedIcon = card.querySelector('.muted-icon');
        const unmutedIcon = card.querySelector('.unmuted-icon');

        playBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            if (video.paused) {
                video.play();
                playIcon.style.display = 'none';
                pauseIcon.style.display = 'inline';
                playLabel.textContent = 'Pause';
            } else {
                video.pause();
                playIcon.style.display = 'inline';
                pauseIcon.style.display = 'none';
                playLabel.textContent = 'Play';
            }
        });

        soundBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            video.muted = !video.muted;
            mutedIcon.style.display = video.muted ? 'inline' : 'none';
            unmutedIcon.style.display = video.muted ? 'none' : 'inline';
            soundBtn.title = video.muted ? 'Unmute' : 'Mute';
        });

        card.querySelector('.download-btn').addEventListener('click', (e) => {
            e.stopPropagation();
            this.downloadImage(videoPath, filename);
        });

        card.querySelector('.card-video').addEventListener('click', () => this.openVideoModal(videoPath));

        // Copy button handlers
        const copyCaptionBtn = card.querySelector('.copy-caption-btn');
        if (copyCaptionBtn) {
            copyCaptionBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.copyToClipboard(caption, copyCaptionBtn);
            });
        }

        const copyHashtagsBtn = card.querySelector('.copy-hashtags-btn');
        if (copyHashtagsBtn) {
            copyHashtagsBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.copyToClipboard(hashtagsStr, copyHashtagsBtn);
            });
        }

        const copyAllBtn = card.querySelector('.copy-all-btn');
        if (copyAllBtn) {
            copyAllBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.copyToClipboard(caption + '\n\n' + hashtagsStr, copyAllBtn);
            });
        }

        // Expand caption handler
        const expandBtn = card.querySelector('.expand-caption-btn');
        if (expandBtn) {
            expandBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                const fullCaption = card.querySelector('.card-caption-full');
                const previewCaption = card.querySelector('.card-caption-text');
                if (expandBtn.dataset.expanded === 'false') {
                    fullCaption.style.display = 'block';
                    previewCaption.style.display = 'none';
                    expandBtn.textContent = 'Show Less ▲';
                    expandBtn.dataset.expanded = 'true';
                } else {
                    fullCaption.style.display = 'none';
                    previewCaption.style.display = 'block';
                    expandBtn.textContent = 'View Full Caption ▼';
                    expandBtn.dataset.expanded = 'false';
                }
            });
        }

        this.contentGrid.insertBefore(card, this.contentGrid.firstChild);
    }

    // Open video in modal (full-screen view)
    openVideoModal(videoPath) {
        // Hide the image element
        this.modalImage.style.display = 'none';

        // Hide the download button (we'll add video-specific download)
        const modalActions = this.modal.querySelector('.modal-actions');
        if (modalActions) modalActions.style.display = 'none';

        // Create video element and insert it after the image
        const video = document.createElement('video');
        video.src = videoPath;
        video.controls = true;
        video.autoplay = true;
        video.loop = true;
        video.className = 'modal-video';
        video.id = 'modalVideo';
        this.modalImage.parentNode.insertBefore(video, this.modalImage.nextSibling);

        // Create video-specific actions (download button)
        const videoActions = document.createElement('div');
        videoActions.className = 'modal-actions modal-video-actions';
        videoActions.innerHTML = `
            <button class="modal-btn modal-video-download">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
                    <polyline points="7 10 12 15 17 10"/>
                    <line x1="12" y1="15" x2="12" y2="3"/>
                </svg>
                Download Video
            </button>
        `;
        video.parentNode.insertBefore(videoActions, video.nextSibling);

        // Download handler
        videoActions.querySelector('.modal-video-download').addEventListener('click', () => {
            const filename = videoPath.split('/').pop();
            this.downloadImage(videoPath, filename);
        });

        // Show modal using hidden attribute (consistent with openModal)
        this.modal.hidden = false;
        document.body.style.overflow = 'hidden';

        // Store cleanup function for closeModal
        this._videoModalCleanup = () => {
            // Remove video element
            const modalVideo = document.getElementById('modalVideo');
            if (modalVideo) modalVideo.remove();
            // Remove video actions
            const vActions = this.modal.querySelector('.modal-video-actions');
            if (vActions) vActions.remove();
            // Restore image and original actions
            this.modalImage.style.display = '';
            if (modalActions) modalActions.style.display = '';
            this._videoModalCleanup = null;
        };
    }
    
    displayHashtags(hashtags) {
        this.hashtagsSection.hidden = false;
        this.hashtagsList.innerHTML = '';
        this.currentHashtags = hashtags;
        
        hashtags.forEach(tag => {
            const span = document.createElement('span');
            span.className = 'hashtag';
            span.textContent = tag;
            span.addEventListener('click', () => {
                navigator.clipboard.writeText(tag);
                span.style.background = 'var(--success)';
                setTimeout(() => { span.style.background = ''; }, 500);
            });
            this.hashtagsList.appendChild(span);
        });
    }
    
    sanitizeImagePath(imagePath) {
        // Clean up malformed image paths that may have markdown artifacts
        if (!imagePath) return null;

        // Decode URL encoding first
        try {
            imagePath = decodeURIComponent(imagePath);
        } catch (e) {
            // Already decoded or invalid
        }

        // Remove markdown prefixes like **📸 Image:** or **Image:**
        imagePath = imagePath.replace(/^\*\*[^*]*\*\*\s*/g, '');
        imagePath = imagePath.replace(/^📸\s*Image:\s*/gi, '');
        imagePath = imagePath.replace(/^Image:\s*/gi, '');

        // Extract path from markdown link format [text](path)
        const linkMatch = imagePath.match(/\[([^\]]*)\]\(([^)]+)\)/);
        if (linkMatch) {
            imagePath = linkMatch[2];
        }

        // Ensure it starts with /generated/ and ends with valid media extension
        if (imagePath.includes('/generated/')) {
            // Extract just the /generated/xxx.ext part (images and videos)
            const genMatch = imagePath.match(/(\/generated\/[a-zA-Z0-9_-]+\.(?:png|jpg|jpeg|gif|webp|mp4|webm|mov))/i);
            if (genMatch) {
                imagePath = genMatch[1];
            }
        }

        // Final validation - accept both image and video formats
        if (!imagePath.startsWith('/generated/') || !imagePath.match(/\.(png|jpg|jpeg|gif|webp|mp4|webm|mov)$/i)) {
            console.warn('Invalid media path after sanitization:', imagePath);
            return null;
        }

        return imagePath;
    }

    async copyToClipboard(text = null, button = null) {
        // If no text provided, use the current caption/hashtags from bottom panel
        if (!text) {
            text = this.currentCaption || '';
            if (this.currentHashtags.length > 0) {
                text += '\n\n' + this.currentHashtags.join(' ');
            }
            button = this.copyCaption;
        }

        try {
            await navigator.clipboard.writeText(text);

            // Show success feedback on the button
            if (button) {
                const originalHtml = button.innerHTML;
                button.innerHTML = '✓ Copied!';
                button.classList.add('copied');
                setTimeout(() => {
                    button.innerHTML = originalHtml;
                    button.classList.remove('copied');
                }, 2000);
            }
        } catch (err) {
            console.error('Copy failed:', err);
        }
    }
    
    openModal(imagePath) {
        this.modalImage.src = imagePath;
        this.modal.hidden = false;
        document.body.style.overflow = 'hidden';
    }
    
    closeModal() {
        // Clean up video modal if it was open
        if (this._videoModalCleanup) {
            this._videoModalCleanup();
        }
        this.modal.hidden = true;
        document.body.style.overflow = '';
    }
    
    downloadCurrentImage() {
        const url = this.modalImage.src;
        const filename = url.split('/').pop();
        this.downloadImage(url, filename);
    }
    
    downloadImage(url, filename) {
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
    
    downloadAll() {
        this.generatedImages.forEach((url, index) => {
            setTimeout(() => {
                const filename = url.split('/').pop();
                this.downloadImage(url, filename);
            }, index * 500);
        });
    }
    
    async refreshGallery() {
        // Only refresh the current session's images, not all images from server
        // This re-renders the gallery with the images we already have in memory
        if (this.generatedImages.length > 0) {
            this.contentGrid.innerHTML = '';
            this.emptyState.hidden = true;
            this.contentGrid.hidden = false;
            this.galleryActions.hidden = false;
            
            // Re-add all session images
            const imagesToReAdd = [...this.generatedImages];
            this.generatedImages = [];
            
            imagesToReAdd.forEach(imgUrl => {
                this.generatedImages.push(imgUrl);
                this.addImageToGallery(imgUrl);
            });
        }
    }
    
    // Load all images from server (only if user explicitly requests)
    async loadAllImages() {
        try {
            const response = await fetch('/generated-images?limit=20');
            const data = await response.json();
            
            if (data.images && data.images.length > 0) {
                this.contentGrid.innerHTML = '';
                this.generatedImages = [];
                this.emptyState.hidden = true;
                this.contentGrid.hidden = false;
                this.galleryActions.hidden = false;
                
                data.images.forEach(img => {
                    if (!this.generatedImages.includes(img.url)) {
                        this.generatedImages.push(img.url);
                        this.addImageToGallery(img.url);
                    }
                });
            }
        } catch (error) {
            console.error('Failed to load images:', error);
        }
    }
    
    // Switch gallery view between all, posts, and campaigns
    switchGalleryView(view) {
        this.galleryViewMode = view;
        
        // Update tab UI
        this.galleryTabs?.forEach(tab => {
            tab.classList.toggle('active', tab.dataset.view === view);
        });
        
        // Filter content based on view
        const allItems = this.contentGrid?.querySelectorAll('.content-card, .campaign-section, .post-card');
        
        allItems?.forEach(item => {
            switch (view) {
                case 'posts':
                    // Show only individual posts/images
                    if (item.classList.contains('campaign-section')) {
                        item.style.display = 'none';
                    } else {
                        item.style.display = '';
                    }
                    break;
                case 'campaigns':
                    // Show only campaigns
                    if (item.classList.contains('campaign-section') || item.classList.contains('campaign-card')) {
                        item.style.display = '';
                    } else {
                        item.style.display = 'none';
                    }
                    break;
                default:
                    // Show all
                    item.style.display = '';
            }
        });
    }

    // =========================================================================
    // STRUCTURED RESPONSE HANDLING (from format_response_for_user tool)
    // =========================================================================

    /**
     * Try to parse structured JSON response from format_response_for_user tool
     * The tool outputs JSON that may be embedded in the agent's response
     * @param {string} text - The full message text
     * @returns {Object|null} Parsed structured response or null
     */
    parseStructuredResponse(text) {
        try {
            // Pattern 0: Tool result wrapper - {'result': '{"text": "...", "has_choices": ...}'}
            // This is a Python dict literal that ADK returns when a tool is called
            // We need to extract the inner JSON string from the 'result' field
            
            // Check if it starts with the wrapper pattern
            if (text.trim().startsWith("{'result':") || text.trim().startsWith('{"result":')) {
                try {
                    // Try to extract using regex first (simpler)
                    const wrapperMatch = text.match(/['"]result['"]\s*:\s*['"]([^'"]+)['"]/);
                    if (wrapperMatch) {
                        let jsonStr = wrapperMatch[1];
                        
                        // Unescape: handle \n, \", \uXXXX, etc.
                        jsonStr = jsonStr
                            .replace(/\\n/g, '\n')
                            .replace(/\\r/g, '\r')
                            .replace(/\\t/g, '\t')
                            .replace(/\\"/g, '"')
                            .replace(/\\'/g, "'")
                            .replace(/\\\\/g, '\\');
                        
                        // Handle unicode escapes like \ud83c\udfa8
                        jsonStr = jsonStr.replace(/\\u([0-9a-fA-F]{4})/g, (match, code) => {
                            return String.fromCharCode(parseInt(code, 16));
                        });
                        
                        const parsed = JSON.parse(jsonStr);
                        if (parsed.text !== undefined && parsed.has_choices !== undefined) {
                            console.log('📋 Parsed tool result wrapper - extracted inner JSON');
                            return parsed;
                        }
                    }
                } catch (e) {
                    console.log('Failed to parse wrapper:', e);
                }
            }
            
            // Pattern 1: Pure JSON response
            if (text.trim().startsWith('{') && text.trim().endsWith('}')) {
                const parsed = JSON.parse(text.trim());
                if (parsed.text !== undefined && parsed.has_choices !== undefined) {
                    console.log('📋 Parsed pure JSON structured response');
                    return parsed;
                }
                // Check if it's wrapped in a result field
                if (parsed.result && typeof parsed.result === 'string') {
                    try {
                        const innerParsed = JSON.parse(parsed.result);
                        if (innerParsed.text !== undefined && innerParsed.has_choices !== undefined) {
                            console.log('📋 Parsed nested result field structured response');
                            return innerParsed;
                        }
                    } catch (e) {
                        // Try unescaping
                        try {
                            const unescaped = parsed.result
                                .replace(/\\n/g, '\n')
                                .replace(/\\"/g, '"')
                                .replace(/\\'/g, "'")
                                .replace(/\\\\/g, '\\');
                            const innerParsed = JSON.parse(unescaped);
                            if (innerParsed.text !== undefined && innerParsed.has_choices !== undefined) {
                                console.log('📋 Parsed nested result field (unescaped) structured response');
                                return innerParsed;
                            }
                        } catch (e2) {
                            // Continue to other patterns
                        }
                    }
                }
            }

            // Pattern 2: JSON embedded in text (tool output)
            // Look for JSON block that contains our expected fields
            const jsonPattern = /\{[^{}]*"text"\s*:\s*"[^"]*"[^{}]*"has_choices"\s*:\s*(true|false)[^{}]*\}/gs;
            const matches = text.match(jsonPattern);

            if (matches) {
                for (const match of matches) {
                    try {
                        const parsed = JSON.parse(match);
                        if (parsed.text !== undefined && parsed.has_choices !== undefined) {
                            console.log('📋 Parsed embedded JSON structured response');
                            return parsed;
                        }
                    } catch (e) {
                        continue;
                    }
                }
            }

            // Pattern 3: Look for JSON with nested choices array
            const complexJsonPattern = /\{[\s\S]*?"text"\s*:\s*"[\s\S]*?"[\s\S]*?"choices"\s*:\s*\[[\s\S]*?\][\s\S]*?\}/g;
            const complexMatches = text.match(complexJsonPattern);

            if (complexMatches) {
                for (const match of complexMatches) {
                    try {
                        // Clean up the match - handle escaped newlines in JSON strings
                        const cleanMatch = match.replace(/\n/g, '\\n');
                        const parsed = JSON.parse(cleanMatch);
                        if (parsed.text !== undefined) {
                            console.log('📋 Parsed complex JSON structured response');
                            return parsed;
                        }
                    } catch (e) {
                        continue;
                    }
                }
            }

            return null;
        } catch (e) {
            console.log('📋 No structured response found, using text fallback');
            return null;
        }
    }

    /**
     * Handle structured response from format_response_for_user tool
     * @param {Object} response - The parsed structured response
     * @param {HTMLElement} messageElement - The message text element to update
     */
    handleStructuredResponse(response, messageElement) {
        console.log('🎯 Handling structured response:', response);

        // Update the message text (render markdown)
        if (messageElement) {
            // Clear any existing content first
            messageElement.innerHTML = '';
            this.updateMessage(messageElement, response.text);
        }

        // Parse for images in the text
        this.parseAssistantResponse(response.text);
        this.updateRightPanel(response.text);

        // Render choices if present
        if (response.has_choices && response.choices && response.choices.length > 0) {
            const contentEl = messageElement?.closest('.message')?.querySelector('.message-content');
            if (contentEl) {
                this.renderStructuredChoiceButtons(response, contentEl);
            }
        }

        // Update input placeholder if provided
        if (response.input_placeholder) {
            this.chatInput.placeholder = response.input_placeholder;
        }

        // Show input hint if provided
        if (response.input_hint && response.allow_free_input) {
            this.showInputHint(response.input_hint);
        }

        // Scroll to bottom after choices render
        setTimeout(() => this.scrollToBottom(), 100);
    }

    /**
     * Render choice buttons from structured response
     * @param {Object} response - The structured response with choices
     * @param {HTMLElement} messageContentElement - The message content element
     */
    renderStructuredChoiceButtons(response, messageContentElement) {
        const { choices, choice_type, allow_free_input, input_hint } = response;

        if (!choices || choices.length === 0) return;

        // Remove any existing choice buttons
        const existingButtons = messageContentElement.querySelector('.choice-buttons-container');
        if (existingButtons) {
            existingButtons.remove();
        }

        const container = document.createElement('div');
        container.className = `choice-buttons-container choice-type-${choice_type || 'single_select'}`;

        choices.forEach(choice => {
            const btn = document.createElement('button');
            btn.className = 'choice-button';
            btn.dataset.choiceId = choice.id;
            btn.dataset.choiceValue = choice.value;

            // Build button content
            let btnContent = '';
            if (choice.icon) {
                btnContent += `<span class="choice-icon">${choice.icon}</span>`;
            }
            btnContent += `<span class="choice-label">${choice.label}</span>`;

            btn.innerHTML = btnContent;

            // Add description as tooltip
            if (choice.description) {
                btn.title = choice.description;

                // Also add as subtitle for menu type
                if (choice_type === 'menu') {
                    btn.innerHTML += `<span class="choice-description">${choice.description}</span>`;
                    btn.classList.add('has-description');
                }
            }

            // Click handler
            btn.addEventListener('click', () => {
                // Send the choice value as the user's message
                this.chatInput.value = choice.value;
                this.sendMessage();

                // Mark this choice as selected and disable all buttons
                container.querySelectorAll('.choice-button').forEach(b => {
                    b.disabled = true;
                    b.classList.add('disabled');
                });
                btn.classList.add('selected');

                // Reset input placeholder
                this.chatInput.placeholder = 'Type your message...';
                this.hideInputHint();
            });

            container.appendChild(btn);
        });

        // Add hint for free input if allowed
        if (allow_free_input && input_hint) {
            const hint = document.createElement('div');
            hint.className = 'choice-input-hint';
            hint.textContent = input_hint;
            container.appendChild(hint);
        }

        messageContentElement.appendChild(container);
    }

    /**
     * Show input hint above the chat input
     * @param {string} hintText - The hint text to display
     */
    showInputHint(hintText) {
        // Remove existing hint
        this.hideInputHint();

        // Place hint ABOVE the input wrapper (in the container), not inside it
        const inputContainer = document.querySelector('.chat-input-container');
        const inputWrapper = document.querySelector('.chat-input-wrapper');
        if (inputContainer && inputWrapper) {
            const hint = document.createElement('div');
            hint.className = 'chat-input-hint';
            hint.textContent = hintText;
            inputContainer.insertBefore(hint, inputWrapper);
        }

        // Also set as placeholder so it's visible in the textarea itself
        if (this.chatInput && hintText) {
            this.chatInput.placeholder = hintText;
        }
    }

    /**
     * Hide the input hint
     */
    hideInputHint() {
        document.querySelector('.chat-input-hint')?.remove();
        if (this.chatInput) {
            this.chatInput.placeholder = 'Type your response...';
        }
    }

    // =========================================================================
    // FALLBACK: TEXT-BASED CHOICE DETECTION AND BUTTON RENDERING
    // =========================================================================

    /**
     * Detect choice options in agent messages and return structured choices
     * This is the fallback when format_response_for_user tool is not used
     * @param {string} text - The message text to analyze
     * @returns {Array} Array of choice objects {icon, label, value, description}
     */
    detectChoicesInMessage(text) {
        const choices = [];
        const seenLabels = new Set();

        // Extended emoji set for matching
        const emojiSet = '📸📅🖼️✨🎬✏️🔄✅❌👍👎📊📝🚀💡🎯🎨📱💼🔥⭐';

        // Pattern 1a: Emoji OUTSIDE bold - 📸 **Single Post** - description
        const emojiOutsidePattern = new RegExp(`([${emojiSet}])\\s*\\*\\*([^*]+)\\*\\*\\s*[-–—:]\\s*([^\\n]+)`, 'g');
        let match;
        while ((match = emojiOutsidePattern.exec(text)) !== null) {
            const icon = match[1].trim();
            const label = match[2].trim();
            const description = match[3].trim();

            if (!seenLabels.has(label.toLowerCase())) {
                seenLabels.add(label.toLowerCase());
                choices.push({
                    icon: icon,
                    label: label,
                    value: label,
                    description: description
                });
            }
        }

        // Pattern 1b: Emoji INSIDE bold - **📸 Single Post** - description (original pattern)
        const emojiInsidePattern = new RegExp(`\\*\\*([${emojiSet}]\\s*[^*]+)\\*\\*\\s*[-–—:]\\s*([^\\n*]+)`, 'g');
        while ((match = emojiInsidePattern.exec(text)) !== null) {
            const fullLabel = match[1].trim();
            const description = match[2].trim();
            const iconMatch = fullLabel.match(new RegExp(`^([${emojiSet}])`));
            const icon = iconMatch ? iconMatch[1] : '';
            const cleanLabel = fullLabel.replace(new RegExp(`^[${emojiSet}]\\s*`), '').trim();

            if (!seenLabels.has(cleanLabel.toLowerCase())) {
                seenLabels.add(cleanLabel.toLowerCase());
                choices.push({
                    icon: icon,
                    label: cleanLabel,
                    value: cleanLabel,
                    description: description
                });
            }
        }

        // Pattern 2: Inline parenthetical choices like (yes / no / skip) or (approve / tweak / skip)
        const inlinePattern = /\(([^)]+(?:\s*\/\s*[^)]+)+)\)/g;
        while ((match = inlinePattern.exec(text)) !== null) {
            const optionsStr = match[1];
            const options = optionsStr.split(/\s*\/\s*/);
            options.forEach(opt => {
                const cleanOpt = opt.trim().replace(/\*\*/g, '');
                if (cleanOpt && !seenLabels.has(cleanOpt.toLowerCase())) {
                    seenLabels.add(cleanOpt.toLowerCase());
                    choices.push({
                        icon: this.getChoiceIcon(cleanOpt),
                        label: cleanOpt,
                        value: cleanOpt,
                        description: ''
                    });
                }
            });
        }

        // Pattern 3: Question-style options ending with ? followed by choices
        // e.g., "Approve Week 1? (yes / tweak something / skip)"
        // Already covered by Pattern 2

        // Pattern 4: "Would you like to:" followed by bullet options
        const bulletOptionsPattern = /(?:would you like to|want to|options|you can)[:.]?\s*\n((?:\s*[-•*]\s*[^\n]+\n?)+)/gi;
        while ((match = bulletOptionsPattern.exec(text)) !== null) {
            const bulletBlock = match[1];
            const bulletPattern = /[-•*]\s*\*?\*?["']?([^"'\n*]+)["']?\*?\*?/g;
            let bulletMatch;
            while ((bulletMatch = bulletPattern.exec(bulletBlock)) !== null) {
                const opt = bulletMatch[1].trim().replace(/[-–—].*$/, '').trim();
                if (opt && opt.length < 50 && !seenLabels.has(opt.toLowerCase())) {
                    seenLabels.add(opt.toLowerCase());
                    choices.push({
                        icon: this.getChoiceIcon(opt),
                        label: opt,
                        value: opt,
                        description: ''
                    });
                }
            }
        }

        // Pattern 5: Numbered concepts/ideas - "1. Title" or "**1. Title**"
        if (choices.length === 0) {
            const numberedPattern = /(?:^|\n)\s*\*?\*?(\d+)\.\s+\*?\*?([^\n*]+?)(?:\*\*)?(?:\n|$)/g;
            const conceptKeywords = /concept|idea|option|video|hook|key message|duration|goal/i;
            
            if (conceptKeywords.test(text)) {
                while ((match = numberedPattern.exec(text)) !== null) {
                    const num = match[1];
                    let title = match[2].trim().replace(/\*\*/g, '');
                    if (title.length > 60) title = title.substring(0, 57) + '...';
                    if (title.length < 3) continue;
                    
                    const emojiMap = {'1': '1️⃣', '2': '2️⃣', '3': '3️⃣', '4': '4️⃣', '5': '5️⃣'};
                    const key = `idea_${num}`;
                    
                    if (!seenLabels.has(key)) {
                        seenLabels.add(key);
                        choices.push({
                            icon: emojiMap[num] || '🔢',
                            label: `Idea ${num}: ${title}`,
                            value: num,
                            description: ''
                        });
                    }
                }
            }
        }

        // Only return choices if we found meaningful options (2-8 choices typically)
        if (choices.length >= 2 && choices.length <= 8) {
            return choices;
        }
        return [];
    }

    /**
     * Get an appropriate icon for a choice based on its text
     */
    getChoiceIcon(text) {
        const lower = text.toLowerCase();
        if (lower.includes('yes') || lower.includes('approve') || lower.includes('confirm')) return '✅';
        if (lower.includes('no') || lower.includes('cancel') || lower.includes('reject')) return '❌';
        if (lower.includes('skip')) return '⏭️';
        if (lower.includes('edit') || lower.includes('tweak') || lower.includes('change')) return '✏️';
        if (lower.includes('done') || lower.includes('finish')) return '🎉';
        if (lower.includes('single') || lower.includes('post')) return '📸';
        if (lower.includes('campaign')) return '📅';
        if (lower.includes('carousel')) return '🖼️';
        if (lower.includes('quick') || lower.includes('image') || lower.includes('general')) return '✨';
        if (lower.includes('animate')) return '🎬';
        if (lower.includes('caption')) return '📝';
        if (lower.includes('hashtag')) return '#️⃣';
        return '';
    }

    /**
     * Render choice buttons below a message
     * @param {Array} choices - Array of choice objects
     * @param {HTMLElement} messageContentElement - The message content element to append to
     */
    renderChoiceButtons(choices, messageContentElement) {
        if (!choices || choices.length === 0) return;

        const container = document.createElement('div');
        container.className = 'choice-buttons-container';

        choices.forEach(choice => {
            const btn = document.createElement('button');
            btn.className = 'choice-button';
            btn.innerHTML = `${choice.icon ? `<span class="choice-icon">${choice.icon}</span>` : ''}${choice.label}`;
            if (choice.description) {
                btn.title = choice.description;
            }

            btn.addEventListener('click', () => {
                // Send the choice as a message
                this.chatInput.value = choice.value;
                this.sendMessage();

                // Mark this choice as selected and disable all buttons
                container.querySelectorAll('.choice-button').forEach(b => {
                    b.disabled = true;
                    b.classList.add('disabled');
                });
                btn.classList.add('selected');
            });

            container.appendChild(btn);
        });

        messageContentElement.appendChild(container);
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    window.app = new MarketingVideoApp();
});
