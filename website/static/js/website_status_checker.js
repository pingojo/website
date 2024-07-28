function getWebsiteStatus(companyId, url) {
    fetch(url)
        .then(response => {
            updateWebsiteStatus(companyId, response.status);
        })
        .catch(error => {
            if (error.name === 'TypeError' && error.message.includes('CORS')) {
                fallbackToServerSideCheck(companyId);
            } else if (error.name === 'TypeError') {
                fallbackToServerSideCheck(companyId);
            } else {

                console.error('Error fetching website status:', error);
            }
        });
}

function updateWebsiteStatus(companyId, status) {
    const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    const data = new FormData();
    data.append('company_id', companyId);
    data.append('status', status);

    fetch('/update_website_status/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken,
            },
            body: data,
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'error') {
                console.error('Error updating website status:', data.message);
            }
        });
}

function fallbackToServerSideCheck(companyId) {
    fetch(`/update_website_status/?company_id=${companyId}`)
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                console.log('Website status (server-side check):', data.website_status);
            } else {
                console.error('Error updating website status:', data.message);
            }
        })
        .catch(error => {
            console.error('Error fetching website status:', error);
        });
}

function checkWebsiteStatus(companyId, url, websiteStatusUpdated) {
    const now = new Date();
    const lastUpdated = new Date(websiteStatusUpdated);

    if (!websiteStatusUpdated || (now - lastUpdated) / (1000 * 60 * 60 * 24) >= 7) {
        getWebsiteStatus(companyId, url);
    }
}