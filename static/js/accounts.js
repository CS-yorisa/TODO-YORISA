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

const withdrawDialog = document.getElementById('withdraw-dialog');
if (withdrawDialog) {
    const withdrawBtn = document.getElementById('withdraw-btn');
    const confirmInput = document.getElementById('withdraw-confirm-input');
    const errorEl = document.getElementById('withdraw-error');
    const isConfirmed = () => confirmInput.value.trim() === withdrawBtn.dataset.confirmText;

    document.getElementById('withdraw-open-btn').addEventListener('click', function () {
        confirmInput.value = '';
        errorEl.style.display = 'none';
        withdrawBtn.disabled = true;
        withdrawDialog.showModal();
        confirmInput.focus();
    });

    document.getElementById('withdraw-cancel-btn').addEventListener('click', function () {
        withdrawDialog.close();
    });

    // 사용자가 '회원 탈퇴'를 정확히 입력해야 탈퇴 버튼이 활성화된다
    confirmInput.addEventListener('input', function () {
        withdrawBtn.disabled = !isConfirmed();
    });

    confirmInput.addEventListener('keydown', function (event) {
        if (event.key === 'Enter' && !event.isComposing && isConfirmed()) {
            withdrawBtn.click();
        }
    });

    withdrawBtn.addEventListener('click', async function () {
        if (!isConfirmed()) {
            return;
        }

        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        errorEl.style.display = 'none';
        withdrawBtn.disabled = true;

        try {
            const response = await fetch(withdrawBtn.dataset.apiUrl, {
                method: 'DELETE',
                headers: { 'X-CSRFToken': csrfToken },
            });

            if (response.ok) {
                // 탈퇴 후 남아 있는 세션을 정리하기 위해 로그아웃 뷰를 거쳐 첫 화면으로 이동
                window.location.href = withdrawBtn.dataset.redirectUrl;
                return;
            }

            const data = await response.json().catch(() => ({}));
            errorEl.textContent = data.detail || '회원 탈퇴에 실패했습니다.';
        } catch (error) {
            errorEl.textContent = '회원 탈퇴에 실패했습니다.';
        }
        errorEl.style.display = 'block';
        withdrawBtn.disabled = false;
    });
}
