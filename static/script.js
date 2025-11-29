async function updateStatus() {
    try {
        const res = await fetch("/api/status");
        const data = await res.json();
        document.getElementById("login").textContent = data.login;
        document.getElementById("display_name").textContent = data.display_name;
        document.getElementById("followers").textContent = data.followers;
        document.getElementById("stream_online").textContent = data.stream_online ? "✓ Sí" : "✗ No";
        document.getElementById("viewer_count").textContent = data.viewer_count;
        document.getElementById("title").textContent = data.title;
    } catch (e) {
        console.error(e);
    }
}

updateStatus();
setInterval(updateStatus, 10000);
