function stripWhitespace(event) {
    const input = event.target;
    const cursorPosition = input.selectionStart;
    const originalLength = input.value.length;

    input.value = input.value.replace(/\s/g, '');

    const removedCount = originalLength - input.value.length;
    input.setSelectionRange(cursorPosition - removedCount, cursorPosition - removedCount);
}

document.querySelectorAll('.js-no-space').forEach(function (input) {
    input.addEventListener('input', stripWhitespace);
});

const passwordEditForm = document.getElementById('password-edit-form');
if (passwordEditForm) {
    passwordEditForm.addEventListener('submit', function (event) {
        const newPassword = passwordEditForm.new_password.value;
        const newPasswordConfirm = passwordEditForm.new_password_confirm.value;
        const errorEl = document.getElementById('password-edit-error');

        if (newPassword !== newPasswordConfirm) {
            event.preventDefault();
            errorEl.textContent = '비밀번호가 일치하지 않습니다.';
            errorEl.style.display = 'block';
        }
    });
}
