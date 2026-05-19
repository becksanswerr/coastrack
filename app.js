const app = {
    init() {
        // Login ekranında bekle
    },
    
    currentUsername: "",

    async login() {
        const u = document.getElementById("login-username").value;
        const p = document.getElementById("login-password").value;
        
        try {
            // Relative URL ensures it works on localhost vs 127.0.0.1 flawlessly
            const res = await fetch("/login", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({username: u, password: p})
            });
            const data = await res.json();
            
            if(data.success) {
                this.currentUsername = u.toLowerCase();
                document.getElementById("p-name").value = data.name;
                document.getElementById("p-age").value = data.age;
                this.navigate("view-profile"); // Profil onay ekranına git
            } else {
                const err = document.getElementById("login-error");
                err.innerText = data.message;
                err.style.display = "block";
            }
        } catch(e) {
            console.error("Login hatası:", e);
        }
    },
    
    async register() {
        const u = document.getElementById("reg-username").value;
        const p = document.getElementById("reg-password").value;
        const n = document.getElementById("reg-name").value;
        const a = parseInt(document.getElementById("reg-age").value) || 20;
        const i = document.getElementById("reg-illness").value || "none";
        
        try {
            const res = await fetch("/register", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({username: u, password: p, name: n, age: a, illness: i})
            });
            const data = await res.json();
            if(data.success) {
                // Return to login screen
                document.getElementById("login-username").value = u;
                document.getElementById("login-password").value = p;
                this.navigate("view-splash");
                alert("Kayıt başarılı! Şimdi giriş yapabilirsiniz.");
            } else {
                const err = document.getElementById("reg-error");
                err.innerText = data.message;
                err.style.display = "block";
            }
        } catch(e) {
            console.error("Register hatası:", e);
        }
    },

    navigate(viewId, navId = null) {
        // Get all views
        const views = document.querySelectorAll('.view');
        
        // Remove active class from all views
        views.forEach(view => {
            if (view.classList.contains('active')) {
                // Optional: add fade-out effect for previous view if needed
                view.classList.remove('active');
            }
        });

        // Add active class to target view
        const targetView = document.getElementById(viewId);
        if (targetView) {
            targetView.classList.add('active');
        }

        // Handle bottom navigation visibility
        const bottomNav = document.getElementById('bottom-nav');
        if (targetView && targetView.classList.contains('with-nav')) {
            bottomNav.classList.remove('hidden');
        } else {
            bottomNav.classList.add('hidden');
        }

        // Update active state on navigation icons
        if (navId) {
            document.querySelectorAll('.nav-item').forEach(item => {
                item.classList.remove('active');
            });
            
            const targetNav = document.getElementById(navId);
            if (targetNav) {
                targetNav.classList.add('active');
            }
        }
    },

    saveProfile() {
        const age = parseInt(document.getElementById("p-age").value) || 20;
        // Check if any medical button was clicked (simplification for demo)
        const isChronic = document.querySelector(".med-btn.active") ? "heart condition" : "none";
        
        // Send to backend AI engine
        if(ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({
                type: "profile",
                age: age,
                illness: isChronic
            }));
            console.log("Kullanıcı profili AI motoruna gönderildi:", {age, illness: isChronic});
        }
        
        this.navigate("view-rides", "nav-rides");
    },
    
    map: null,
    marker: null,
    
    updateMap(lat, lng) {
        if (!this.map) {
            // Haritayı başlat
            this.map = L.map('map').setView([lat, lng], 16);
            L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
                attribution: '&copy; OpenStreetMap &copy; CARTO',
                maxZoom: 19
            }).addTo(this.map);
            
            // Özel Coastrack Pin'i
            const icon = L.divIcon({
                className: 'custom-pin',
                html: '<div style="background-color: #344CB7; width: 20px; height: 20px; border-radius: 50%; border: 3px solid white; box-shadow: 0 0 10px rgba(0,0,0,0.5);"></div>',
                iconSize: [20, 20]
            });
            this.marker = L.marker([lat, lng], {icon: icon}).addTo(this.map);
        } else {
            // Pin konumunu güncelle
            this.marker.setLatLng([lat, lng]);
            this.map.setView([lat, lng]);
        }
    }
};

let ws;

function initWebSocket() {
    // Determine the host based on where it's being served
    const host = window.location.host || "localhost:8000";
    ws = new WebSocket("ws://" + host + "/ws");
    
    ws.onopen = function() {
        console.log("WebSocket bağlantısı kuruldu.");
    };
    
    ws.onmessage = function(event) {
        try {
            const data = JSON.parse(event.data);
            
            // Sadece giriş yapmış olan kullanıcının verilerini mobil arayüzde göster
            if(data.type === "sensor" && data.username === app.currentUsername) {
                // UI Güncelleme (Nabız ve Oksijen)
                const bpmEl = document.getElementById("bpm-val");
                const spo2El = document.getElementById("spo2-val");
                if(bpmEl) bpmEl.innerText = data.hr;
                if(spo2El) spo2El.innerText = data.spo2 + "%";
                // Haritada Konumu Güncelle
                if(data.lat && data.lng) {
                    app.updateMap(data.lat, data.lng);
                }

                // AI Risk Analiz Sonucu: Backend'den CRITICAL_ALERT gelirse!
                if(data.alert === "CRITICAL_ALERT") {
                    const emergencyView = document.getElementById("view-emergency");
                    if(emergencyView && !emergencyView.classList.contains("active")) {
                        console.log("⚠️ YAPAY ZEKA UYARISI:", data.reason);
                        app.navigate("view-emergency", "nav-emergency");
                        
                        // Uyarı metnini AI'nin gönderdiği sebeple değiştir
                        const reasonText = document.querySelector(".emergency-content p");
                        if(reasonText) {
                            reasonText.innerHTML = `<strong>Durum Tespiti:</strong> ${data.reason}<br><br><span style="color: #444; font-size: 0.95rem;">💡 <b>Öneri:</b> Lütfen güvenli bir alana geçip dinlenin. İhtiyaç halinde park görevlilerine başvurun.</span>`;
                            reasonText.style.color = "red";
                        }
                        
                        // Uyarı ikonunun daha hızlı çarpmasını sağla
                        const warningCircle = document.querySelector(".warning-circle");
                        if(warningCircle) {
                            warningCircle.style.animationDuration = "0.5s";
                        }
                    }
                }
            }
        } catch(e) {
            console.error("WebSocket veri hatası:", e);
        }
    };
    
    ws.onclose = function() {
        console.log("WebSocket bağlantısı kesildi. Yeniden bağlanılıyor...");
        setTimeout(initWebSocket, 2000);
    };
}

// Initialize application when DOM is fully loaded
document.addEventListener('DOMContentLoaded', () => {
    app.init();
    initWebSocket(); // WebSocket'i başlat
    
    // Add simple interaction effects for lists
    document.querySelectorAll('.list-item').forEach(item => {
        item.addEventListener('click', function(e) {
            if(!e.target.closest('.add-btn')) {
                this.style.transform = 'scale(0.98)';
                setTimeout(() => {
                    this.style.transform = 'scale(1)';
                }, 150);
            }
        });
    });
    
    // Medical buttons toggle logic
    document.querySelectorAll('.med-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            this.classList.toggle('active');
            if(this.classList.contains('active')) {
                this.style.backgroundColor = '#FF3B30'; // Red color to indicate selected
            } else {
                this.style.backgroundColor = 'var(--brand-blue)';
            }
        });
    });
});
