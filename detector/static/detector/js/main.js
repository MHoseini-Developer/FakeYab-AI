
// ============================================
// AI Forensic Vision — Interactive Script
// ============================================


// ============================================
// GENERAL PAGE FEATURES
// ============================================

document.addEventListener('DOMContentLoaded', function () {

    // ---------- منوی موبایل ----------
    const toggleBtn = document.getElementById('mobileToggle');
    const nav = document.querySelector('.main-nav');

    if (toggleBtn && nav) {
        toggleBtn.addEventListener('click', function () {

            nav.classList.toggle('open');

            const icon = this.querySelector('i');

            if (icon) {
                if (nav.classList.contains('open')) {
                    icon.className = 'fas fa-times';
                } else {
                    icon.className = 'fas fa-bars';
                }
            }
        });
    }


    // ---------- Contact: ترمینال تعاملی ----------
    const terminalInput = document.getElementById('terminalInput');

    if (terminalInput) {

        terminalInput.addEventListener('keydown', function (e) {

            if (e.key === 'Enter') {

                const msg = this.value.trim();

                if (msg) {

                    const terminalBody = this.closest('.terminal-body');

                    if (terminalBody) {

                        const newLine = document.createElement('p');

                        newLine.innerHTML = `
                            <span style="color: #4ade80;">></span>
                            <span style="color: #e5e9f0;">${msg}</span>
                        `;

                        terminalBody.insertBefore(
                            newLine,
                            this.parentElement
                        );

                        this.value = '';

                        terminalBody.scrollTop =
                            terminalBody.scrollHeight;
                    }
                }
            }
        });
    }


    // ---------- کلیک روی کارت‌های لایه ----------
    document.querySelectorAll('.layer-card').forEach(card => {

        card.addEventListener('click', function () {

            this.style.borderColor = '#818cf8';

            setTimeout(() => {
                this.style.borderColor = '';
            }, 400);

        });

    });


    console.log('🔍 AI Forensic Vision v2.4.0 — System Ready');
    console.log('📊 Detection Engine: EfficientNet-B4 + Cross-Attention');

});


// ============================================
// ANALYZE PAGE
// ============================================

// ---------- عناصر صفحه ----------
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const browseBtn = document.getElementById('browseBtn');

const uploadStatus = document.getElementById('uploadStatus');
const statusDot = document.querySelector('.status-dot');
const statusText = document.querySelector('.status-text');

const resultGrid = document.getElementById('resultGrid');

const resetBtn = document.getElementById('resetBtn');
const pdfBtn = document.getElementById('pdfBtn');

const summaryTime = document.getElementById('summaryTime');

// ------تعریف عناصر نتیجه ----------
const summaryStatus = document.getElementById('summaryStatus');
const summaryConfidence = document.getElementById('summaryConfidence');

const synthBar = document.getElementById('synthBar');
const synthValue = document.getElementById('synthValue');

const authBar = document.getElementById('authBar');
const authValue = document.getElementById('authValue');

const modelBadge = document.getElementById('modelBadge');
const modelText = document.getElementById('modelText');

// ============================================
// CSRF TOKEN
// ============================================

function getCSRFToken() {

    const csrfInput = document.querySelector(
        '[name=csrfmiddlewaretoken]'
    );

    if (!csrfInput) {
        console.error('❌ CSRF token not found.');
        return null;
    }

    return csrfInput.value;
}


// ============================================
// SEND IMAGE TO DJANGO API
// ============================================

async function sendImage(file) {

    if (!file) {
        return;
    }


    // ---------- وضعیت اولیه ----------
    if (statusText) {
        statusText.textContent = `📎 ${file.name}`;
    }

    if (statusDot) {
        statusDot.className = 'status-dot analyzing';
    }

    if (uploadStatus) {
        uploadStatus.style.borderColor = '#fbbf24';
    }


    // ---------- ساخت FormData ----------
    const formData = new FormData();

    formData.append('image', file);


    // ---------- دریافت CSRF ----------
    const csrftoken = getCSRFToken();

    if (!csrftoken) {

        if (statusText) {
            statusText.textContent = '❌ Security token not found.';
        }

        return;
    }


    // ---------- ارسال به Django ----------
    try {

        console.log('📤 Sending image to Django API...');
        console.log('📁 Filename:', file.name);
        console.log('📦 Size:', file.size, 'bytes');


        const response = await fetch('/api/analyze/', {

            method: 'POST',

            headers: {
                'X-CSRFToken': csrftoken,
            },

            body: formData,

        });


        // ---------- بررسی پاسخ ----------
        if (!response.ok) {

            const text = await response.text();

            console.error(
                '❌ API Error:',
                response.status,
                text
            );

            if (statusDot) {
                statusDot.className = 'status-dot idle';
            }

            if (uploadStatus) {
                uploadStatus.style.borderColor = '#ef4444';
            }

            if (statusText) {
                statusText.textContent =
                    `❌ Analysis failed (${response.status})`;
            }

            return;
        }


        // ---------- دریافت JSON ----------
        const data = await response.json();


        console.log('✅ API Response:', data);


        // ---------- وضعیت موفق ----------
        if (statusDot) {
            statusDot.className = 'status-dot done';
        }

        if (uploadStatus) {
            uploadStatus.style.borderColor = '#4ade80';
        }


        // ---------- نتیجه مدل ----------

        const result = data.result;

        const confidence = data.confidence * 100;
        const fakeProbability = data.fake_probability * 100;
        const realProbability = data.real_probability * 100;
        const processingTime = data.processing_time;


        // ---------- Summary ----------

        if (summaryStatus) {
            summaryStatus.textContent =
                result === 'FAKE' ? 'بله' : 'خیر';
        }

        if (summaryConfidence) {
            summaryConfidence.textContent =
                confidence.toFixed(2) + '%';
        }
        if (summaryTime) {
            summaryTime.textContent =
                processingTime.toFixed(2) + ' ثانیه';
        }


        // ---------- Probability: Fake ----------

        if (synthBar) {
            synthBar.style.width =
                fakeProbability.toFixed(2) + '%';
        }

        if (synthValue) {
            synthValue.textContent =
                fakeProbability.toFixed(2) + '%';
        }


        // ---------- Probability: Real ----------

        if (authBar) {
            authBar.style.width =
                realProbability.toFixed(2) + '%';
        }

        if (authValue) {
            authValue.textContent =
                realProbability.toFixed(2) + '%';
        }


        // ---------- Model Card ----------

        if (modelBadge) {
            modelBadge.textContent = result;
        }

        if (modelText) {
            modelText.textContent =
                result === 'FAKE'
                    ? `مدل تصویر را با احتمال ${fakeProbability.toFixed(2)}٪ ساخته‌شده توسط هوش مصنوعی تشخیص داده است.`
                    : `مدل تصویر را با احتمال ${realProbability.toFixed(2)}٪ واقعی تشخیص داده است.`;
        }


        // ---------- وضعیت ----------

        if (statusText) {
            statusText.textContent =
                result === 'FAKE'
                    ? '⚠️ تصویر احتمالاً ساخته‌شده با هوش مصنوعی است.'
                    : '✅ تصویر احتمالاً واقعی است.';
        }


        // ---------- نمایش نتیجه ----------

        if (resultGrid) {
            resultGrid.style.display = 'flex';
            resultGrid.style.opacity = '1';
        }


        // ---------- نمایش در Console ----------
        console.log('🎯 Result:', result);
        console.log(
            '📊 Confidence:',
            confidence.toFixed(2) + '%'
        );
        console.log(
            '🤖 Fake:',
            fakeProbability.toFixed(2) + '%'
        );
        console.log(
            '📷 Real:',
            realProbability.toFixed(2) + '%'
        );


    } catch (error) {

        console.error(
            '❌ Request failed:',
            error
        );


        if (statusDot) {
            statusDot.className = 'status-dot idle';
        }

        if (uploadStatus) {
            uploadStatus.style.borderColor = '#ef4444';
        }

        if (statusText) {
            statusText.textContent =
                '❌ Could not connect to server.';
        }
    }
}


// ============================================
// BROWSE BUTTON
// ============================================

if (browseBtn && fileInput) {

    browseBtn.addEventListener('click', function (e) {

        e.preventDefault();

        e.stopPropagation();

        fileInput.click();

    });


    // ---------- انتخاب فایل ----------
    fileInput.addEventListener('change', function () {

        if (!this.files || !this.files[0]) {
            return;
        }

        const file = this.files[0];

        sendImage(file);

    });

}


// ============================================
// DRAG & DROP
// ============================================

if (uploadArea) {

    // ---------- Drag Over ----------
    uploadArea.addEventListener('dragover', function (e) {

        e.preventDefault();

        this.classList.add('dragover');

    });


    // ---------- Drag Leave ----------
    uploadArea.addEventListener('dragleave', function (e) {

        e.preventDefault();

        this.classList.remove('dragover');

    });


    // ---------- Drop ----------
    uploadArea.addEventListener('drop', function (e) {

        e.preventDefault();

        this.classList.remove('dragover');

        const files = e.dataTransfer.files;

        if (files && files[0]) {

            const file = files[0];

            sendImage(file);

        }

    });


    // ---------- کلیک روی فضای آپلود ----------
    uploadArea.addEventListener('click', function () {

        if (fileInput) {
            fileInput.click();
        }

    });

}


// ============================================
// RESET
// ============================================

if (resetBtn) {

    resetBtn.addEventListener('click', function () {

        if (resultGrid) {
            resultGrid.style.display = 'none';
        }


        if (statusDot) {
            statusDot.className = 'status-dot idle';
        }


        if (statusText) {
            statusText.textContent =
                'Awaiting input...';
        }


        if (uploadStatus) {
            uploadStatus.style.borderColor =
                '#1e293b';
        }


        if (fileInput) {
            fileInput.value = '';
        }

    });

}


// ============================================
// PDF BUTTON — فعلاً شبیه‌سازی
// ============================================

if (pdfBtn) {

    pdfBtn.addEventListener('click', function () {

        this.innerHTML =
            '<i class="fas fa-spinner fa-spin"></i> Generating PDF...';

        this.disabled = true;


        setTimeout(() => {

            this.innerHTML =
                '<i class="fas fa-file-pdf"></i> Export Full Report (PDF)';

            this.disabled = false;


            const msg = document.createElement('div');

            msg.style.cssText =
                'color:#4ade80; font-size:0.9rem; margin-top:0.5rem;';

            msg.textContent =
                '✅ Report downloaded successfully!';


            this.parentElement.appendChild(msg);


            setTimeout(() => {

                msg.remove();

            }, 4000);

        }, 1500);

    });

}
