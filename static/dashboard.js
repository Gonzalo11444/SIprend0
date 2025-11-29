// Cambiar pestañas
document.querySelectorAll(".tab-link").forEach(btn => {
    btn.addEventListener("click", e => {
        e.preventDefault();
        // Quitar active de todos
        document.querySelectorAll(".tab-link").forEach(a => a.classList.remove("active"));
        btn.classList.add("active");

        const tab = btn.getAttribute("data-tab");
        document.querySelectorAll(".tab").forEach(t => t.style.display = "none");
        document.getElementById(tab).style.display = "block";
    });
});

// Actualizar datos
async function loadTwitch() {
    const res = await fetch("/api/twitch");
    const data = await res.json();
    document.getElementById("followers").textContent = data.followers;
    document.getElementById("status").textContent = data.stream_online ? "En directo 🔴" : "Offline ⚫";
    document.getElementById("viewers").textContent = data.viewer_count;
    document.getElementById("title").textContent = data.title;
}
setInterval(loadTwitch, 5000);
loadTwitch();

async function loadYouTube() {
    const res = await fetch("/api/youtube");
    const data = await res.json();
    document.getElementById("yt_subs").textContent = data.subscribers;
    document.getElementById("yt_views").textContent = data.views_total;
    document.getElementById("yt_last_title").textContent = data.latest_video_title;
    document.getElementById("yt_last_thumb").src = data.latest_video_thumbnail;
}
setInterval(loadYouTube, 10000);
loadYouTube();
