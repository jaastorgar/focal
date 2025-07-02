document.addEventListener('DOMContentLoaded', () => {
    const buttonsContainer = document.querySelector('.perfil-buttons');
    const sections = document.querySelectorAll('.perfil-section');
    const buttons = document.querySelectorAll('.perfil-buttons button');

    if (!buttonsContainer || sections.length === 0 || buttons.length === 0) {
        return;
    }

    const switchTab = (targetId) => {
        sections.forEach(section => {
            section.classList.remove('visible');
        });
        buttons.forEach(button => {
            button.classList.remove('active');
        });

        const targetSection = document.getElementById(targetId);
        const targetButton = document.querySelector(`button[data-target="${targetId}"]`);
        
        if (targetSection) {
            targetSection.classList.add('visible');
        }
        if (targetButton) {
            targetButton.classList.add('active');
        }
    };

    buttonsContainer.addEventListener('click', (event) => {
        const targetButton = event.target.closest('button[data-target]');
        if (targetButton) {
            const targetId = targetButton.dataset.target;
            if (targetId) {
                switchTab(targetId);
            }
        }
    });

    if (buttons.length > 0) {
        const firstTargetId = buttons[0].dataset.target;
        if (firstTargetId) {
            switchTab(firstTargetId);
        }
    }
});