function toggleNav() {
    const n = document.getElementById("navlinks");
    n.classList.toggle("open");
}


function showToast(msg) {

    let t = document.getElementById("toast");

    if (!t) {
        t = document.createElement("div");
        t.id = "toast";
        document.body.appendChild(t);
    }

    t.textContent = msg;

    t.classList.add("show");

    clearTimeout(window.tt);

    window.tt = setTimeout(
        () => t.classList.remove("show"),
        2800
    );
}


/* =========================
   FAVORITES
========================= */

async function toggleFavorite(button) {

    const businessId = button.dataset.businessId;

    if (!businessId) {
        showToast("Business ID not found.");
        return;
    }

    try {

        const response = await fetch(
            `/api/favorite/${businessId}`,
            {
                method: "POST"
            }
        );

        const data = await response.json();


        /* USER NOT LOGGED IN */

        if (response.status === 401) {

            alert("Please login first.");

            window.location.href = "/login";

            return;
        }


        /* FAVORITE UPDATED */

        if (data.success) {

            if (data.favorite) {

                button.textContent = "♥";

                button.classList.add("liked");

                showToast("Added to favorites ❤️");

            } else {

                button.textContent = "♡";

                button.classList.remove("liked");

                showToast("Removed from favorites.");

            }

        } else {

            showToast(
                data.message || "Something went wrong."
            );

        }

    } catch (error) {

        console.error("Favorite error:", error);

        showToast("Unable to update favorite.");

    }

}


function searchHome() {

    const q =
        (document.getElementById("heroSearch")?.value || "")
        .trim();

    if (!q) {

        showToast("Type something to search.");

        return;
    }

    window.location.href =
        "/businesses?search=" + encodeURIComponent(q);
}


function filterExplore() {

    const q =
        (document.getElementById("exploreInput")?.value || "")
        .toLowerCase();

    document
        .querySelectorAll(".explore-item")
        .forEach(x => {

            x.style.display =
                x.dataset.name
                .toLowerCase()
                .includes(q)
                ? ""
                : "none";

        });

}


function filterBusinesses() {

    const q =
        (document.getElementById("businessInput")?.value || "")
        .toLowerCase();

    document
        .querySelectorAll(".business-item")
        .forEach(x => {

            x.style.display =
                x.dataset.name
                .toLowerCase()
                .includes(q)
                ? ""
                : "none";

        });

}


function nearMe() {

    const m =
        document.getElementById("locationMsg");

    if (!navigator.geolocation) {

        m.textContent =
            "Location is not supported by your browser.";

        return;
    }

    m.textContent =
        "Requesting location permission...";

    navigator.geolocation.getCurrentPosition(

        () => {

            m.textContent =
                "Location received — nearby discovery will be connected in the next stage.";

        },

        () => {

            m.textContent =
                "Location permission was not allowed.";

        }

    );

}
function toggleCategoryDropdown() {
    const menu = document.getElementById("categoryMenu");

    if (menu.style.display === "none" || menu.style.display === "") {
        menu.style.display = "block";
    } else {
        menu.style.display = "none";
    }
}