const app = {
    init() {
        // Login ekranında bekle
    },
    
    currentUsername: "",
    userPoints: 0,

    async login() {
        const u = document.getElementById("login-username").value;
        const p = document.getElementById("login-password").value;
        
        try {
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
                document.getElementById("p-illness").value = data.illness || "none";
                document.getElementById("p-allergies").value = data.allergies || "none";
                this.refreshUserInfo();
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
        const allergies = document.getElementById("reg-allergies").value || "none";
        const emergencyContact = document.getElementById("reg-emergency").value || "none";
        
        try {
            const res = await fetch("/register", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({username: u, password: p, name: n, age: a, illness: i, allergies: allergies, emergency_contact: emergencyContact})
            });
            const data = await res.json();
            if(data.success) {
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
        const views = document.querySelectorAll('.view');
        views.forEach(view => {
            if (view.classList.contains('active')) {
                view.classList.remove('active');
            }
        });

        const targetView = document.getElementById(viewId);
        if (targetView) {
            targetView.classList.add('active');
        }

        const bottomNav = document.getElementById('bottom-nav');
        if (targetView && targetView.classList.contains('with-nav')) {
            bottomNav.classList.remove('hidden');
        } else {
            bottomNav.classList.add('hidden');
        }

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
        const illness = document.getElementById("p-illness").value || "none";
        const allergies = document.getElementById("p-allergies").value || "none";
        
        fetch('/update_profile', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                username: this.currentUsername,
                age: age,
                illness: illness,
                allergies: allergies
            })
        });
        
        this.navigate("view-rides", "nav-rides");
    },
    
    async refreshUserInfo() {
        try {
            const res = await fetch(`/get_user_info?username=${this.currentUsername}`);
            const data = await res.json();
            if(data.success) {
                this.userPoints = data.points;
                const pointsEl = document.getElementById("wallet-points");
                if(pointsEl) pointsEl.innerText = this.userPoints + " CP";
            }
        } catch(e) {
            console.error(e);
        }
    },
    
    async scanRide(rideName, buttonElement) {
        const originalText = buttonElement.innerHTML;
        buttonElement.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Loading...`;
        try {
            const res = await fetch("/scan_ride", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({username: this.currentUsername, ride_name: rideName})
            });
            const data = await res.json();
            if(data.success) {
                this.userPoints = data.total_points;
                alert(`Tebrikler! ${rideName} oyuncağına bindiniz ve ${data.points_earned} CP kazandınız! Toplam: ${this.userPoints} CP`);
                this.refreshUserInfo();
                buttonElement.innerHTML = `<i class="fa-solid fa-check"></i> Enjoy!`;
                buttonElement.style.background = "#34C759";
            }
        } catch(e) {
            console.error(e);
            buttonElement.innerHTML = originalText;
        }
    },

    map: null,
    marker: null,
    
    updateMap(lat, lng) {
        if (!this.map) {
            this.map = L.map('map').setView([lat, lng], 16);
            L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
                attribution: '&copy; OpenStreetMap &copy; CARTO',
                maxZoom: 19
            }).addTo(this.map);
            
            const icon = L.divIcon({
                className: 'custom-pin',
                html: '<div style="background-color: #344CB7; width: 20px; height: 20px; border-radius: 50%; border: 3px solid white; box-shadow: 0 0 10px rgba(0,0,0,0.5);"></div>',
                iconSize: [20, 20]
            });
            this.marker = L.marker([lat, lng], {icon: icon}).addTo(this.map);
        } else {
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
                // Haritada Konumu Güncelle
                if(data.lat && data.lng) {
                    app.updateMap(data.lat, data.lng);
                }
                
                // Vitals and SOS updates are intentionally hidden from user UI per request.
                // Logs view can manually refresh to pull data.
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
