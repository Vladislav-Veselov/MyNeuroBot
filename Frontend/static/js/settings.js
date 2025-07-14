document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('settings-form');
    const messageDiv = document.getElementById('message');
    const messageContent = document.getElementById('message-content');

    // Load existing settings
    loadSettings();

    // Handle radio button styling
    const radioButtons = document.querySelectorAll('input[type="radio"]');
    radioButtons.forEach(radio => {
        radio.addEventListener('change', function() {
            // Remove selected styling from all radio buttons in the same group
            const name = this.name;
            document.querySelectorAll(`input[name="${name}"]`).forEach(rb => {
                const label = rb.closest('label');
                const circle = label.querySelector('div');
                circle.className = 'w-4 h-4 border-2 border-[#718096] rounded-full mr-3 flex-shrink-0';
            });

            // Add selected styling to the checked radio button
            if (this.checked) {
                const label = this.closest('label');
                const circle = label.querySelector('div');
                circle.className = 'w-4 h-4 border-2 border-[#DC4918] rounded-full mr-3 flex-shrink-0 bg-[#DC4918]';
            }
        });
    });

    // Handle form submission
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const formData = new FormData(form);
        const settings = {
            tone: formData.get('tone'),
            humor: parseInt(formData.get('humor')),
            brevity: parseInt(formData.get('brevity')),
            additional_prompt: formData.get('additional_prompt')
        };

        // Validate tone selection
        if (!settings.tone) {
            showMessage('Пожалуйста, выберите тон общения', 'error');
            return;
        }

        // Save settings
        fetch('/api/save_settings', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(settings)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showMessage('Настройки успешно сохранены!', 'success');
            } else {
                showMessage(data.error || 'Ошибка при сохранении настроек', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showMessage('Ошибка при сохранении настроек', 'error');
        });
    });

    function loadSettings() {
        fetch('/api/get_settings')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const settings = data.settings;
                
                // Set tone
                if (settings.tone) {
                    const toneRadio = document.querySelector(`input[name="tone"][value="${settings.tone}"]`);
                    if (toneRadio) {
                        toneRadio.checked = true;
                        toneRadio.dispatchEvent(new Event('change'));
                    }
                }

                // Set humor level
                if (settings.humor !== undefined) {
                    document.querySelector('input[name="humor"]').value = settings.humor;
                }

                // Set brevity level
                if (settings.brevity !== undefined) {
                    document.querySelector('input[name="brevity"]').value = settings.brevity;
                }

                // Set additional prompt
                if (settings.additional_prompt) {
                    document.getElementById('additional-prompt').value = settings.additional_prompt;
                }
            }
        })
        .catch(error => {
            console.error('Error loading settings:', error);
        });
    }

    function showMessage(text, type) {
        messageContent.textContent = text;
        messageDiv.className = `mt-4 p-4 rounded-lg ${type === 'success' ? 'bg-green-900 text-green-200' : 'bg-red-900 text-red-200'}`;
        messageDiv.classList.remove('hidden');
        
        // Hide message after 5 seconds
        setTimeout(() => {
            messageDiv.classList.add('hidden');
        }, 5000);
    }
}); 