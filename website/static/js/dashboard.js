

    $(document).ready(function () {
        const form = $('#job-url-form');
        const urlInput = $('#job-url');

        // Drag and drop functionality
        urlInput.on('dragover', function (e) {
            e.preventDefault();
            e.stopPropagation();
            $(this).addClass('dragging');
        });

        urlInput.on('dragleave', function (e) {
            e.preventDefault();
            e.stopPropagation();
            $(this).removeClass('dragging');
        });

        urlInput.on('drop', function (e) {
            e.preventDefault();
            e.stopPropagation();
            $(this).removeClass('dragging');
            const url = e.originalEvent.dataTransfer.getData('text/plain');
            $(this).val(url);
            submitForm();
        });

        form.on('submit', function (e) {
            e.preventDefault();
            submitForm();
        });

        function submitForm() {
            const url = urlInput.val();
            if (url) {
                // Call the Django view to scrape the job details
                axios.get('{% url "scrape-job" %}', {
                        params: {
                            url: url
                        }
                    })
                    .then(response => {
                        const {
                            job_title,
                            company_name
                        } = response.data;
                        // Populate the fields with the scraped data
                        // ...
                        // Submit the form data with the application details
                        // ...
                    })
                    .catch(error => {
                        console.error('Error scraping job:', error);
                    });
            }
        }
    });