/**
 * تطبيق القرآن الكريم متعدد الروايات
 * يعمل مع API قاعدة البيانات
 */

// الحالة العامة
const state = {
    currentRiwayah: 'hafs',
    currentPage: 1,
    totalPages: 604,
    selectedAyah: null,
    reciters: [],
    currentReciter: null,
    currentMoshafId: null,
    isPlaying: false,
    activeTab: 'tafseer',
    // حالة الصوت
    audio: null,
    currentSura: 1,
    currentAyah: 1,
    ayahTimings: [],
    audioLoaded: false
};

// العناصر
const elements = {
    riwayahSelect: document.getElementById('riwayah-select'),
    mushafContent: document.getElementById('mushaf-content'),
    pageInput: document.getElementById('page-input'),
    totalPages: document.getElementById('total-pages'),
    btnPrev: document.getElementById('btn-prev'),
    btnNext: document.getElementById('btn-next'),
    pageInfoSura: document.getElementById('page-info-sura'),
    pageInfoJuz: document.getElementById('page-info-juz'),
    pageInfoHizb: document.getElementById('page-info-hizb'),
    sidebar: document.getElementById('sidebar'),
    sidebarContent: document.getElementById('sidebar-content'),
    sidebarTitle: document.getElementById('sidebar-title'),
    infoPanel: document.getElementById('info-panel'),
    panelContent: document.getElementById('panel-content'),
    tabTafseer: document.getElementById('tab-tafseer'),
    tabTranslation: document.getElementById('tab-translation'),
    audioPlayer: document.getElementById('audio-player'),
    reciterSelect: document.getElementById('reciter-select'),
    searchModal: document.getElementById('search-modal'),
    searchInput: document.getElementById('search-input'),
    searchResults: document.getElementById('search-results')
};

// ==================== API Functions ====================

const API = {
    baseUrl: '/api',
    
    async get(endpoint) {
        try {
            const response = await fetch(`${this.baseUrl}${endpoint}`);
            if (!response.ok) throw new Error('API Error');
            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            return null;
        }
    },
    
    async getRiwayat() {
        return this.get('/riwayat');
    },
    
    async getPage(pageNum, riwayah = state.currentRiwayah) {
        return this.get(`/page/${pageNum}?riwayah=${riwayah}`);
    },
    
    async getSurahs(riwayah = state.currentRiwayah) {
        return this.get(`/surahs?riwayah=${riwayah}`);
    },
    
    async getJuzs(riwayah = state.currentRiwayah) {
        return this.get(`/juzs?riwayah=${riwayah}`);
    },
    
    async getAhzab(riwayah = state.currentRiwayah) {
        return this.get(`/ahzab?riwayah=${riwayah}`);
    },
    
    async getTafseer(sura, aya) {
        return this.get(`/tafseer/${sura}/${aya}`);
    },
    
    async getTranslation(sura, aya, lang = 'en') {
        return this.get(`/translation/${sura}/${aya}?lang=${lang}`);
    },
    
    async getReciters(riwayah = state.currentRiwayah) {
        return this.get(`/reciters?riwayah=${riwayah}`);
    },
    
    async search(query, riwayah = state.currentRiwayah) {
        return this.get(`/search?q=${encodeURIComponent(query)}&riwayah=${riwayah}`);
    },
    
    async getStats() {
        return this.get('/stats');
    },
    
    async getTimings(reciterId, sura, moshafId) {
        return this.get(`/timings/${reciterId}/${sura}?moshaf_id=${moshafId}`);
    }
};

// ==================== Rendering Functions ====================

async function loadPage(pageNum) {
    state.currentPage = pageNum;
    elements.pageInput.value = pageNum;
    
    // عرض التحميل
    elements.mushafContent.innerHTML = '<div class="loading">جاري التحميل...</div>';
    
    // تحميل الصفحة
    const pageData = await API.getPage(pageNum);
    
    if (!pageData || !pageData.lines) {
        elements.mushafContent.innerHTML = '<div class="loading">خطأ في تحميل الصفحة</div>';
        return;
    }
    
    // تحديث معلومات الصفحة
    updatePageInfo(pageData);
    
    // عرض الأسطر
    renderLines(pageData.lines);
}

function renderLines(lines) {
    elements.mushafContent.innerHTML = '';
    elements.mushafContent.className = `mushaf-content ${state.currentRiwayah}`;
    
    // التأكد من وجود 15 سطر
    const displayLines = [...lines];
    while (displayLines.length < 15) {
        displayLines.push({ type: 'empty', text: '' });
    }
    
    displayLines.forEach((line, index) => {
        const lineEl = document.createElement('div');
        lineEl.className = `line ${line.type || 'ayat'}`;
        lineEl.textContent = line.text || '';
        
        // إضافة بيانات للسطر
        if (line.sura_no) {
            lineEl.dataset.sura = line.sura_no;
            
            // تخزين جميع أرقام الآيات في السطر
            if (line.aya_numbers) {
                try {
                    const ayaNumbers = typeof line.aya_numbers === 'string' 
                        ? JSON.parse(line.aya_numbers) 
                        : line.aya_numbers;
                    if (ayaNumbers && ayaNumbers.length > 0) {
                        lineEl.dataset.aya = ayaNumbers[0];
                        lineEl.dataset.ayaNumbers = JSON.stringify(ayaNumbers);
                    }
                } catch (e) {}
            }
        }
        
        // حدث النقر
        lineEl.addEventListener('click', () => handleLineClick(line));
        
        elements.mushafContent.appendChild(lineEl);
    });
}

async function updatePageInfo(pageData) {
    // تحديث معلومات السورة
    if (pageData.lines && pageData.lines.length > 0) {
        // البحث عن أول سورة في الصفحة
        const firstSuraLine = pageData.lines.find(l => l.sura_name && l.type !== 'empty');
        if (firstSuraLine) {
            elements.pageInfoSura.textContent = `سورة ${firstSuraLine.sura_name}`;
            state.currentSura = firstSuraLine.sura_no || 1;
        } else {
            elements.pageInfoSura.textContent = `صفحة ${state.currentPage}`;
        }
    }
    
    // تحديث الجزء
    if (pageData.juz) {
        elements.pageInfoJuz.textContent = `الجزء ${pageData.juz}`;
        
        // حساب الحزب
        const hizb = Math.ceil((pageData.juz * 2) - (state.currentPage > 300 ? 0 : 1));
        elements.pageInfoHizb.textContent = `الحزب ${Math.min(hizb, 60)}`;
    }
}

// ==================== Event Handlers ====================

function handleLineClick(line) {
    if (!line.sura_no || line.type === 'header' || line.type === 'empty') return;
    
    let ayaNo = null;
    try {
        const ayaNumbers = typeof line.aya_numbers === 'string' 
            ? JSON.parse(line.aya_numbers) 
            : line.aya_numbers;
        if (ayaNumbers && ayaNumbers.length > 0) {
            ayaNo = ayaNumbers[0];
        }
    } catch (e) {}
    
    if (!ayaNo) return;
    
    state.selectedAyah = { sura: line.sura_no, aya: ayaNo };
    
    // فتح لوحة المعلومات
    elements.infoPanel.classList.remove('hidden');
    
    // تحميل التفسير أو الترجمة
    if (state.activeTab === 'tafseer') {
        loadTafseer(line.sura_no, ayaNo);
    } else {
        loadTranslation(line.sura_no, ayaNo);
    }
}

async function loadTafseer(sura, aya) {
    elements.panelContent.innerHTML = '<div class="loading">جاري التحميل...</div>';
    
    const tafseer = await API.getTafseer(sura, aya);
    
    if (tafseer && tafseer.tafseer_text) {
        elements.panelContent.innerHTML = `
            <div class="ayah-info">سورة ${sura} - آية ${aya}</div>
            <div class="tafseer-text">${tafseer.tafseer_text}</div>
        `;
    } else {
        elements.panelContent.innerHTML = '<p class="hint">لا يوجد تفسير متاح لهذه الآية</p>';
    }
}

async function loadTranslation(sura, aya) {
    elements.panelContent.innerHTML = '<div class="loading">جاري التحميل...</div>';
    
    const translation = await API.getTranslation(sura, aya);
    
    if (translation && translation.translation) {
        elements.panelContent.innerHTML = `
            <div class="ayah-info">Surah ${sura} - Ayah ${aya}</div>
            <div class="translation-text">${translation.translation}</div>
            ${translation.footnotes ? `<div class="footnotes">${translation.footnotes}</div>` : ''}
        `;
    } else {
        elements.panelContent.innerHTML = '<p class="hint">No translation available</p>';
    }
}

async function loadSurahIndex() {
    elements.sidebarTitle.textContent = 'فهرس السور';
    elements.sidebarContent.innerHTML = '<div class="loading">جاري التحميل...</div>';
    elements.sidebar.classList.remove('hidden');
    
    const surahs = await API.getSurahs();
    
    if (!surahs) {
        elements.sidebarContent.innerHTML = '<p>خطأ في التحميل</p>';
        return;
    }
    
    elements.sidebarContent.innerHTML = surahs.map(surah => `
        <div class="index-item" onclick="goToPage(${surah.start_page}); closeSidebar();">
            <div class="index-main">
                <span class="index-number">${surah.number}</span>
                <div class="index-details">
                    <span class="index-name">${surah.name_ar}</span>
                    <span class="index-sub">${surah.ayat_count} آية</span>
                </div>
            </div>
            <span class="index-page">ص ${surah.start_page}</span>
        </div>
    `).join('');
}

async function loadJuzIndex() {
    elements.sidebarTitle.textContent = 'فهرس الأجزاء';
    elements.sidebarContent.innerHTML = '<div class="loading">جاري التحميل...</div>';
    elements.sidebar.classList.remove('hidden');
    
    const juzs = await API.getJuzs();
    
    if (!juzs) {
        elements.sidebarContent.innerHTML = '<p>خطأ في التحميل</p>';
        return;
    }
    
    elements.sidebarContent.innerHTML = juzs.map(juz => `
        <div class="index-item" onclick="goToPage(${juz.start_page}); closeSidebar();">
            <div class="index-main">
                <span class="index-number">${juz.number}</span>
                <span class="index-name">الجزء ${juz.number}</span>
            </div>
            <span class="index-page">ص ${juz.start_page}</span>
        </div>
    `).join('');
}

async function loadAhzabIndex() {
    elements.sidebarTitle.textContent = 'فهرس الأحزاب';
    elements.sidebarContent.innerHTML = '<div class="loading">جاري التحميل...</div>';
    elements.sidebar.classList.remove('hidden');
    
    const ahzab = await API.getAhzab();
    
    if (!ahzab) {
        elements.sidebarContent.innerHTML = '<p>خطأ في التحميل</p>';
        return;
    }
    
    elements.sidebarContent.innerHTML = ahzab.map(hizb => `
        <div class="index-item" onclick="goToPage(${hizb.start_page}); closeSidebar();">
            <div class="index-main">
                <span class="index-number">${hizb.hizb_num}</span>
                <div class="index-details">
                    <span class="index-name">الحزب ${hizb.hizb_num}</span>
                    <span class="index-sub">${hizb.start_sura_name || ''} - آية ${hizb.start_aya || 1}</span>
                </div>
            </div>
            <span class="index-page">ص ${hizb.start_page}</span>
        </div>
    `).join('');
}

function closeSidebar() {
    elements.sidebar.classList.add('hidden');
}

async function loadReciters() {
    const reciters = await API.getReciters();
    
    if (!reciters || reciters.length === 0) {
        elements.reciterSelect.innerHTML = '<option value="">لا يوجد قراء لهذه الرواية</option>';
        state.reciters = [];
        return;
    }
    
    state.reciters = reciters;
    
    // إزالة التكرارات (نفس القارئ قد يكون له أكثر من مصحف)
    const uniqueReciters = [];
    const seen = new Set();
    for (const r of reciters) {
        const key = `${r.reciter_id}_${r.moshaf_id}`;
        if (!seen.has(key)) {
            seen.add(key);
            uniqueReciters.push(r);
        }
    }
    
    elements.reciterSelect.innerHTML = '<option value="">🎧 اختر قارئ</option>' +
        uniqueReciters.map(r => `<option value="${r.reciter_id}_${r.moshaf_id}">${r.name_ar}</option>`).join('');
}

async function performSearch() {
    const query = elements.searchInput.value.trim();
    if (query.length < 2) {
        elements.searchResults.innerHTML = '<p class="hint">أدخل كلمتين على الأقل</p>';
        return;
    }
    
    elements.searchResults.innerHTML = '<div class="loading">جاري البحث...</div>';
    
    const results = await API.search(query);
    
    if (!results || results.count === 0) {
        elements.searchResults.innerHTML = '<p class="hint">لا توجد نتائج</p>';
        return;
    }
    
    elements.searchResults.innerHTML = results.results.map(r => `
        <div class="search-result-item" onclick="goToPage(${r.page}); closeSearchModal();">
            <div class="surah-name">${r.sura_name || 'سورة ' + r.sura_no} - آية ${r.aya_no}</div>
            <div class="ayah-text">${r.text.substring(0, 100)}...</div>
        </div>
    `).join('');
}

// ==================== Navigation ====================

function goToPage(pageNum) {
    if (pageNum < 1) pageNum = 1;
    if (pageNum > state.totalPages) pageNum = state.totalPages;
    loadPage(pageNum);
}

function nextPage() {
    goToPage(state.currentPage + 1);
}

function prevPage() {
    goToPage(state.currentPage - 1);
}

// ==================== Modal Functions ====================

function openSearchModal() {
    elements.searchModal.classList.remove('hidden');
    elements.searchInput.focus();
}

function closeSearchModal() {
    elements.searchModal.classList.add('hidden');
}

// ==================== Audio Player Functions ====================

async function initAudioPlayer() {
    state.audio = new Audio();
    
    // أحداث الصوت
    state.audio.addEventListener('timeupdate', handleTimeUpdate);
    state.audio.addEventListener('ended', handleAudioEnded);
    state.audio.addEventListener('loadedmetadata', handleAudioLoaded);
    state.audio.addEventListener('error', handleAudioError);
    
    // عناصر المشغل
    elements.btnPlay = document.getElementById('btn-play');
    elements.btnPrevAyah = document.getElementById('btn-prev-ayah');
    elements.btnNextAyah = document.getElementById('btn-next-ayah');
    elements.progressBar = document.getElementById('progress-bar');
    elements.currentTime = document.getElementById('current-time');
    elements.totalTime = document.getElementById('total-time');
    elements.playerReciter = document.getElementById('player-reciter');
    elements.playerSurah = document.getElementById('player-surah');
}

async function selectReciter(reciterId, moshafId) {
    const reciter = state.reciters.find(r => r.reciter_id == reciterId && r.moshaf_id == moshafId);
    if (!reciter) return;
    
    state.currentReciter = reciter;
    state.currentMoshafId = moshafId;
    
    // إظهار المشغل
    elements.audioPlayer.classList.remove('hidden');
    elements.playerReciter.textContent = reciter.name_ar;
    
    // تحميل السورة الحالية
    await loadSurahAudio(state.currentSura);
}

async function loadSurahAudio(suraNo) {
    if (!state.currentReciter) return;
    
    state.currentSura = suraNo;
    state.currentAyah = 1;
    
    // تحميل التوقيتات
    const timings = await API.getTimings(
        state.currentReciter.reciter_id, 
        suraNo, 
        state.currentMoshafId
    );
    
    if (timings && timings.length > 0) {
        state.ayahTimings = timings;
    } else {
        state.ayahTimings = [];
    }
    
    // تحميل الملف الصوتي
    const audioUrl = `${state.currentReciter.server_url}${String(suraNo).padStart(3, '0')}.mp3`;
    state.audio.src = audioUrl;
    state.audioLoaded = false;
    
    // تحديث واجهة المشغل
    elements.playerSurah.textContent = `سورة ${suraNo}`;
    elements.progressBar.value = 0;
    elements.currentTime.textContent = '0:00';
    
    console.log('تحميل الصوت:', audioUrl);
}

function togglePlay() {
    if (!state.audio.src) return;
    
    if (state.isPlaying) {
        state.audio.pause();
        state.isPlaying = false;
        elements.btnPlay.textContent = '▶';
    } else {
        state.audio.play();
        state.isPlaying = true;
        elements.btnPlay.textContent = '⏸';
    }
}

function playAyah(ayahNo) {
    if (!state.ayahTimings.length) {
        // إذا لم تكن هناك توقيتات، شغّل من البداية
        state.audio.currentTime = 0;
        state.audio.play();
        state.isPlaying = true;
        elements.btnPlay.textContent = '⏸';
        return;
    }
    
    const timing = state.ayahTimings.find(t => t.aya_no === ayahNo);
    if (timing) {
        state.currentAyah = ayahNo;
        state.audio.currentTime = timing.start_time / 1000; // تحويل من ميلي ثانية
        state.audio.play();
        state.isPlaying = true;
        elements.btnPlay.textContent = '⏸';
        
        // تحديث تمييز الآية
        highlightCurrentAyah();
    }
}

function nextAyah() {
    const nextAyahNo = state.currentAyah + 1;
    const timing = state.ayahTimings.find(t => t.aya_no === nextAyahNo);
    
    if (timing) {
        playAyah(nextAyahNo);
    } else {
        // الانتقال للسورة التالية
        if (state.currentSura < 114) {
            loadSurahAudio(state.currentSura + 1).then(() => {
                playAyah(1);
            });
        }
    }
}

function prevAyah() {
    if (state.currentAyah > 1) {
        playAyah(state.currentAyah - 1);
    } else if (state.currentSura > 1) {
        // الانتقال للسورة السابقة
        loadSurahAudio(state.currentSura - 1).then(() => {
            if (state.ayahTimings.length > 0) {
                playAyah(state.ayahTimings[state.ayahTimings.length - 1].aya_no);
            }
        });
    }
}

function handleTimeUpdate() {
    if (!state.audio.duration) return;
    
    const currentMs = state.audio.currentTime * 1000;
    const progress = (state.audio.currentTime / state.audio.duration) * 100;
    
    elements.progressBar.value = progress;
    elements.currentTime.textContent = formatTime(state.audio.currentTime);
    
    // تحديد الآية الحالية من التوقيتات
    if (state.ayahTimings.length > 0) {
        for (let i = state.ayahTimings.length - 1; i >= 0; i--) {
            if (currentMs >= state.ayahTimings[i].start_time) {
                if (state.currentAyah !== state.ayahTimings[i].aya_no) {
                    state.currentAyah = state.ayahTimings[i].aya_no;
                    highlightCurrentAyah();
                }
                break;
            }
        }
    }
}

function handleAudioLoaded() {
    state.audioLoaded = true;
    elements.totalTime.textContent = formatTime(state.audio.duration);
}

function handleAudioEnded() {
    state.isPlaying = false;
    elements.btnPlay.textContent = '▶';
    
    // الانتقال للسورة التالية تلقائياً
    if (state.currentSura < 114) {
        loadSurahAudio(state.currentSura + 1).then(() => {
            playAyah(1);
        });
    }
}

function handleAudioError(e) {
    console.error('خطأ في تحميل الصوت:', e);
    state.isPlaying = false;
    elements.btnPlay.textContent = '▶';
}

function seekAudio(e) {
    if (!state.audio.duration) return;
    
    const percent = e.target.value;
    state.audio.currentTime = (percent / 100) * state.audio.duration;
}

function formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

function highlightCurrentAyah() {
    // إزالة التمييز السابق
    document.querySelectorAll('.line.playing').forEach(el => {
        el.classList.remove('playing');
    });
    
    // تمييز جميع الأسطر التي تحتوي على الآية الحالية
    const lines = document.querySelectorAll('.line');
    lines.forEach(line => {
        // التحقق من أن السطر يحتوي على الآية الحالية
        const suraNo = parseInt(line.dataset.sura);
        const ayaNumbers = line.dataset.ayaNumbers;
        
        if (suraNo === state.currentSura && ayaNumbers) {
            try {
                const ayaList = JSON.parse(ayaNumbers);
                if (ayaList.includes(state.currentAyah)) {
                    line.classList.add('playing');
                }
            } catch (e) {
                // fallback للطريقة القديمة
                if (parseInt(line.dataset.aya) === state.currentAyah) {
                    line.classList.add('playing');
                }
            }
        }
    });
}

// ==================== Initialization ====================

async function init() {
    console.log('تهيئة التطبيق...');
    
    // تحميل الإحصائيات
    const stats = await API.getStats();
    if (stats) {
        console.log('إحصائيات قاعدة البيانات:', stats);
    }
    
    // تهيئة مشغل الصوت
    await initAudioPlayer();
    
    // تحميل الصفحة الأولى
    await loadPage(1);
    
    // تحميل القراء
    await loadReciters();
    
    // ربط الأحداث
    setupEventListeners();
    
    console.log('تم تهيئة التطبيق بنجاح');
}

function setupEventListeners() {
    // تغيير الرواية
    elements.riwayahSelect.addEventListener('change', async (e) => {
        state.currentRiwayah = e.target.value;
        await loadPage(state.currentPage);
        await loadReciters();
    });
    
    // التنقل
    elements.btnPrev.addEventListener('click', prevPage);
    elements.btnNext.addEventListener('click', nextPage);
    
    elements.pageInput.addEventListener('change', (e) => {
        goToPage(parseInt(e.target.value) || 1);
    });
    
    // لوحة المفاتيح
    document.addEventListener('keydown', (e) => {
        if (e.key === 'ArrowRight') prevPage();
        if (e.key === 'ArrowLeft') nextPage();
        if (e.key === 'Escape') {
            closeSearchModal();
            elements.sidebar.classList.add('hidden');
            elements.infoPanel.classList.add('hidden');
        }
    });
    
    // الفهارس
    document.getElementById('btn-surahs').addEventListener('click', loadSurahIndex);
    document.getElementById('btn-juzs').addEventListener('click', loadJuzIndex);
    document.getElementById('btn-ahzab').addEventListener('click', loadAhzabIndex);
    document.getElementById('btn-close-sidebar').addEventListener('click', closeSidebar);
    
    // البحث
    document.getElementById('btn-search').addEventListener('click', openSearchModal);
    document.getElementById('btn-do-search').addEventListener('click', performSearch);
    elements.searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') performSearch();
    });
    
    // التبويبات
    elements.tabTafseer.addEventListener('click', () => {
        state.activeTab = 'tafseer';
        elements.tabTafseer.classList.add('active');
        elements.tabTranslation.classList.remove('active');
        if (state.selectedAyah) {
            loadTafseer(state.selectedAyah.sura, state.selectedAyah.aya);
        }
    });
    
    elements.tabTranslation.addEventListener('click', () => {
        state.activeTab = 'translation';
        elements.tabTranslation.classList.add('active');
        elements.tabTafseer.classList.remove('active');
        if (state.selectedAyah) {
            loadTranslation(state.selectedAyah.sura, state.selectedAyah.aya);
        }
    });
    
    // إغلاق لوحة المعلومات
    document.getElementById('btn-close-panel').addEventListener('click', () => {
        elements.infoPanel.classList.add('hidden');
    });
    
    // إغلاق نافذة البحث
    elements.searchModal.addEventListener('click', (e) => {
        if (e.target === elements.searchModal) closeSearchModal();
    });
    
    // مشغل الصوت
    elements.reciterSelect.addEventListener('change', (e) => {
        const value = e.target.value;
        if (value) {
            const [reciterId, moshafId] = value.split('_');
            selectReciter(parseInt(reciterId), parseInt(moshafId));
        }
    });
    
    elements.btnPlay.addEventListener('click', togglePlay);
    elements.btnPrevAyah.addEventListener('click', prevAyah);
    elements.btnNextAyah.addEventListener('click', nextAyah);
    elements.progressBar.addEventListener('input', seekAudio);
    
    // تشغيل الآية عند النقر المزدوج
    elements.mushafContent.addEventListener('dblclick', (e) => {
        const line = e.target.closest('.line');
        if (line && line.dataset.sura && line.dataset.aya) {
            const sura = parseInt(line.dataset.sura);
            const aya = parseInt(line.dataset.aya);
            
            if (state.currentReciter) {
                if (state.currentSura !== sura) {
                    loadSurahAudio(sura).then(() => {
                        playAyah(aya);
                    });
                } else {
                    playAyah(aya);
                }
            }
        }
    });
}

// بدء التطبيق
document.addEventListener('DOMContentLoaded', init);

