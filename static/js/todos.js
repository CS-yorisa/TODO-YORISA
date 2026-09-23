function toggleCategoryEditMode() {
    const sidebar = document.querySelector('.category-sidebar');
    const btn = document.getElementById('category-edit-toggle');
    sidebar.classList.toggle('edit-mode');
    btn.classList.toggle('active');
    clearCategorySelection();
}

function onCategoryCheckChange() {
    const ids = Array.from(document.querySelectorAll('.category-edit-check:checked')).map(cb => cb.dataset.id);
    document.getElementById('category-delete-ids').value = ids.join(',');
    document.getElementById('category-delete-bar').style.display = ids.length > 0 ? 'block' : 'none';
}

function clearCategorySelection() {
    document.querySelectorAll('.category-edit-check').forEach(cb => cb.checked = false);
    const idsInput = document.getElementById('category-delete-ids');
    if (idsInput) idsInput.value = '';
    const bar = document.getElementById('category-delete-bar');
    if (bar) bar.style.display = 'none';
}

function toggleTodoDeleteMode() {
    const list = document.getElementById('todo-list');
    const btn = document.getElementById('todo-delete-toggle');
    const bar = document.getElementById('todo-delete-bar');
    const isOn = list.classList.toggle('delete-mode');
    btn.classList.toggle('active');
    clearTodoSelection();
    bar.style.display = isOn ? 'flex' : 'none';
}

function onTodoCheckChange() {
    const ids = Array.from(document.querySelectorAll('.todo-card__bulk-check:checked')).map(cb => cb.dataset.id);
    document.getElementById('todo-delete-ids').value = ids.join(',');
    updateTodoDeleteBarState(ids.length);
}

function clearTodoSelection() {
    document.querySelectorAll('.todo-card__bulk-check').forEach(cb => cb.checked = false);
    const idsInput = document.getElementById('todo-delete-ids');
    if (idsInput) idsInput.value = '';
    updateTodoDeleteBarState(0);
}

function updateTodoDeleteBarState(count) {
    const countEl = document.getElementById('todo-delete-count');
    const submitBtn = document.getElementById('todo-delete-submit');
    if (!countEl || !submitBtn) return;
    if (count > 0) {
        countEl.textContent = `🗑️ ${count}개 삭제 예정`;
        submitBtn.disabled = false;
    } else {
        countEl.textContent = '⚠️ 삭제할 항목을 선택하세요';
        submitBtn.disabled = true;
    }
}

function setActiveCategory(btn) {
    document.querySelectorAll('.category-list__item').forEach(b => b.classList.remove('category-list__item--active'));
    btn.classList.add('category-list__item--active');
}

function setActiveTab(btn) {
    document.querySelectorAll('.status-filter__btn').forEach(b => b.classList.remove('status-filter__btn--active'));
    btn.classList.add('status-filter__btn--active');
}

function togglePicker(id, event) {
    event.stopPropagation();
    const picker = document.getElementById('picker-' + id);
    const isOpen = picker.classList.contains('status-picker--open');
    document.querySelectorAll('.status-picker--open').forEach(p => p.classList.remove('status-picker--open'));
    if (!isOpen) picker.classList.add('status-picker--open');
}

function closePicker(id) {
    document.getElementById('picker-' + id).classList.remove('status-picker--open');
}

document.addEventListener('click', function() {
    document.querySelectorAll('.status-picker--open').forEach(p => p.classList.remove('status-picker--open'));
    document.querySelectorAll('.category-picker--open').forEach(p => p.classList.remove('category-picker--open'));
});

function openDuePicker(btn) {
    const input = btn.nextElementSibling;
    if (input && input._flatpickr) input._flatpickr.open();
}

const MONTHS_KO = ['1월', '2월', '3월', '4월', '5월', '6월', '7월', '8월', '9월', '10월', '11월', '12월'];

function setupMonthPicker(fp) {
    const cal = fp.calendarContainer;
    if (cal._monthPickerReady) return;
    cal._monthPickerReady = true;

    const monthSelect = cal.querySelector('.flatpickr-monthDropdown-months');
    if (!monthSelect) return;

    const trigger = document.createElement('button');
    trigger.type = 'button';
    trigger.className = 'fp-month-trigger';
    trigger.textContent = MONTHS_KO[fp.currentMonth];

    const grid = document.createElement('div');
    grid.className = 'fp-month-grid';
    MONTHS_KO.forEach((name, i) => {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'fp-month-option';
        btn.textContent = name;
        btn.addEventListener('mousedown', function(e) {
            e.preventDefault(); e.stopPropagation();
            fp.changeMonth(i, false);
            grid.classList.remove('open');
        });
        grid.appendChild(btn);
    });

    trigger.addEventListener('mousedown', function(e) {
        e.preventDefault(); e.stopPropagation();
        grid.classList.toggle('open');
        if (grid.classList.contains('open')) syncMonthGrid(fp, grid);
    });
    cal.addEventListener('mousedown', function(e) {
        if (!grid.contains(e.target) && e.target !== trigger) grid.classList.remove('open');
    });

    monthSelect.replaceWith(trigger);
    cal.appendChild(grid);
    fp._fpTrigger = trigger;
    fp._fpGrid = grid;
}

function syncMonthGrid(fp, grid) {
    grid.querySelectorAll('.fp-month-option').forEach((btn, i) => btn.classList.toggle('active', i === fp.currentMonth));
}

function updateMonthTrigger(fp) {
    if (fp._fpTrigger) fp._fpTrigger.textContent = MONTHS_KO[fp.currentMonth];
    if (fp._fpGrid) syncMonthGrid(fp, fp._fpGrid);
}

function initDueDatePickers() {
    document.querySelectorAll('.due-date-input').forEach(input => {
        if (input._flatpickr) return;
        const isAddForm = input.id === 'add-due-date';
        flatpickr(input, {
            locale: 'ko',
            dateFormat: 'Y-m-d',
            disableMobile: true,
            onReady: function(_, __, fp) { setupMonthPicker(fp); },
            onMonthChange: function(_, __, fp) { updateMonthTrigger(fp); },
            onChange: function(dates, dateStr) {
                if (isAddForm) updateAddDueDateBtn(dateStr);
                else input.form.requestSubmit();
            }
        });
    });
}

function updateAddDueDateBtn(dateStr) {
    const btn = document.getElementById('add-due-btn');
    const dBadge = document.getElementById('add-d-day-badge');
    if (!btn) return;
    btn.classList.remove('due-badge--none', 'due-badge--upcoming', 'due-badge--today', 'due-badge--overdue');
    if (typeof dateStr === 'string' && dateStr) {
        const [y, m, d] = dateStr.split('-').map(Number);
        const picked = new Date(y, m - 1, d);
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        const diffDays = Math.round((picked - today) / 86400000);
        const dLabel = diffDays === 0 ? 'D-DAY' : diffDays > 0 ? `D-${diffDays}` : '';
        btn.textContent = `📅 ${y}/${m}/${d}`;
        btn.classList.add('due-badge--upcoming');
        if (dBadge) {
            dBadge.textContent = dLabel;
            dBadge.className = 'd-day-badge' + (dLabel ? ' d-day-badge--' + (diffDays === 0 ? 'today' : 'upcoming') : '');
            dBadge.style.display = dLabel ? 'inline-block' : 'none';
        }
    } else {
        btn.textContent = '📅 기한 추가';
        btn.classList.add('due-badge--none');
        if (dBadge) dBadge.style.display = 'none';
    }
}

function resetAddDueDateBtn() {
    const input = document.getElementById('add-due-date');
    if (!input) return;
    if (input._flatpickr) input._flatpickr.clear();
    else input.value = '';
    updateAddDueDateBtn('');
}

document.addEventListener('DOMContentLoaded', initDueDatePickers);
document.addEventListener('htmx:afterSettle', initDueDatePickers);

function setAddCategory(id, btn) {
    document.getElementById('add-category-id').value = id;
    const trigger = document.querySelector('#cat-picker-add .todo-card__tag--btn');
    trigger.className = trigger.className.replace(/\bcat-color-\d\b/g, '').trim();
    if (id) {
        trigger.textContent = btn.textContent;
        trigger.classList.remove('todo-add-cat-btn--empty');
        const colorClass = btn.dataset.colorClass;
        if (colorClass) trigger.classList.add(colorClass);
    } else {
        trigger.textContent = '+ 카테고리';
        trigger.classList.add('todo-add-cat-btn--empty');
    }
    document.querySelectorAll('#cat-picker-add .category-picker__option').forEach(b => b.classList.remove('category-picker__option--active'));
    btn.classList.add('category-picker__option--active');
    closeCatPicker('add');
}

function resetAddCategoryPicker() {
    const idInput = document.getElementById('add-category-id');
    if (idInput) idInput.value = '';
    const trigger = document.querySelector('#cat-picker-add .todo-card__tag--btn');
    if (trigger) {
        trigger.textContent = '+ 카테고리';
        trigger.className = trigger.className.replace(/\bcat-color-\d\b/g, '').trim();
        trigger.classList.add('todo-add-cat-btn--empty');
    }
    document.querySelectorAll('#cat-picker-add .category-picker__option').forEach(b => b.classList.remove('category-picker__option--active'));
    const noneBtn = document.querySelector('#cat-picker-add .category-picker__option--none');
    if (noneBtn) noneBtn.classList.add('category-picker__option--active');
}

function toggleCatPicker(id, event) {
    event.stopPropagation();
    const picker = document.getElementById('cat-picker-' + id);
    const isOpen = picker.classList.contains('category-picker--open');
    document.querySelectorAll('.category-picker--open').forEach(p => p.classList.remove('category-picker--open'));
    if (!isOpen) picker.classList.add('category-picker--open');
}

function closeCatPicker(id) {
    document.getElementById('cat-picker-' + id).classList.remove('category-picker--open');
}

// ===== 변경 후 자동 갱신 =====
// 카드·카테고리 변경 요청은 한 영역만 교체하므로, 요청이 끝나면 현재 보고 있는 조건 그대로
// #todo-section 전체(+ 사이드바 OOB)를 다시 불러와 필터·개수·선택지를 최신 상태로 맞춘다.

function getCurrentTodoSectionUrl() {
    if (document.querySelector('.todo-due-banner--active')) return '/todos/?due=week';

    const activeTab = document.querySelector('.status-filter__btn--active');
    const params = new URL(activeTab ? activeTab.getAttribute('hx-get') : '/todos/', location.origin).searchParams;
    const status = params.get('status') || '';

    // 보고 있던 카테고리가 삭제되었으면 전체 보기로 돌아간다
    let categoryId = document.getElementById('current-category-id')?.value || '';
    if (categoryId && !document.querySelector(`.category-edit-check[data-id="${categoryId}"]`)) {
        categoryId = '';
    }
    return `/todos/?category=${categoryId}&status=${status}`;
}

function refreshTodoSection() {
    return htmx.ajax('GET', getCurrentTodoSectionUrl(), { target: '#todo-section', swap: 'innerHTML' });
}

const handledTodoRequests = new WeakSet();

document.addEventListener('htmx:afterSettle', function (evt) {
    const { xhr, requestConfig, pathInfo } = evt.detail;
    if (!xhr || handledTodoRequests.has(xhr)) return;
    if (requestConfig?.verb !== 'post' || !pathInfo?.requestPath?.startsWith('/todos/')) return;
    if (xhr.status < 200 || xhr.status >= 300) return;
    handledTodoRequests.add(xhr);
    refreshTodoSection();
});

// ===== 할 일 상세보기 / 수정 =====

let todoDetailData = null;

function formatDueDate(dateStr) {
    if (!dateStr) return '';
    const [y, m, d] = dateStr.split('-').map(Number);
    return `${y}/${m}/${d}`;
}

function showTodoDetailError(elId, message) {
    const errorEl = document.getElementById(elId);
    errorEl.textContent = message;
    errorEl.style.display = message ? 'block' : 'none';
}

function renderTodoDetailView(todo) {
    const statusLabel = document.querySelector(`#todo-detail-status-labels [data-value="${todo.status}"]`);
    const categoryLabel = todo.category_id
        ? document.querySelector(`#todo-detail-category-labels [data-value="${todo.category_id}"]`)
        : null;

    const statusEl = document.getElementById('todo-detail-status');
    statusEl.textContent = statusLabel ? statusLabel.textContent : todo.status;
    statusEl.className = `todo-card__status todo-card__status--${todo.status}`;

    const categoryEl = document.getElementById('todo-detail-category');
    categoryEl.textContent = categoryLabel ? categoryLabel.textContent : '카테고리 없음';
    categoryEl.className = 'todo-card__tag ' + (categoryLabel ? `cat-color-${todo.category_id % 8}` : 'todo-add-cat-btn--empty');

    document.getElementById('todo-detail-title').textContent = todo.title;
    document.getElementById('todo-detail-due').textContent = todo.due_date
        ? `📅 ${formatDueDate(todo.due_date)}`
        : '📅 기한 없음';

    const descEl = document.getElementById('todo-detail-desc');
    descEl.textContent = todo.description || '설명이 없어요.';
    descEl.classList.toggle('todo-detail__desc--empty', !todo.description);
}

function fillTodoDetailForm(todo) {
    document.getElementById('todo-detail-input-title').value = todo.title;
    document.getElementById('todo-detail-input-desc').value = todo.description;
}

function setTodoDetailMode(mode) {
    const isEdit = mode === 'edit';
    if (isEdit) fillTodoDetailForm(todoDetailData);
    showTodoDetailError('todo-detail-error', '');
    document.getElementById('todo-detail-view').style.display = isEdit ? 'none' : 'block';
    document.getElementById('todo-detail-form').style.display = isEdit ? 'flex' : 'none';
    if (isEdit) document.getElementById('todo-detail-input-title').focus();
}

async function openTodoDetail(id) {
    const dialog = document.getElementById('todo-detail-dialog');
    try {
        const response = await fetch(`/api/todos/${id}/`);
        if (!response.ok) throw new Error();
        todoDetailData = await response.json();
    } catch (error) {
        alert('할 일 정보를 불러오지 못했습니다.');
        return;
    }
    renderTodoDetailView(todoDetailData);
    setTodoDetailMode('view');
    dialog.showModal();
}

function closeTodoDetail() {
    document.getElementById('todo-detail-dialog').close();
}

document.addEventListener('submit', async function (evt) {
    const form = evt.target;
    if (form.id !== 'todo-detail-form') return;
    evt.preventDefault();

    // form.title은 폼 자체의 title 속성을 가리키므로 elements로 접근한다
    const fields = form.elements;
    // 상태·카테고리·기한은 카드에서 바로 수정하므로 여기서는 제목·설명만 다룬다
    const values = {
        title: fields.title.value.trim(),
        description: fields.description.value,
    };
    if (!values.title) {
        showTodoDetailError('todo-detail-error', '제목을 입력해 주세요.');
        return;
    }

    // 바뀐 필드만 PATCH로 보낸다
    const payload = {};
    Object.keys(values).forEach(key => {
        if (values[key] !== todoDetailData[key]) payload[key] = values[key];
    });
    if (Object.keys(payload).length === 0) {
        setTodoDetailMode('view');
        return;
    }

    const saveBtn = document.getElementById('todo-detail-save');
    saveBtn.disabled = true;
    try {
        const response = await fetch(`/api/todos/${todoDetailData.id}/`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': fields.csrfmiddlewaretoken.value,
            },
            body: JSON.stringify(payload),
        });
        if (!response.ok) {
            const data = await response.json().catch(() => ({}));
            const message = response.status === 422 || typeof data.detail !== 'string'
                ? '입력값을 확인해 주세요.'
                : data.detail;
            showTodoDetailError('todo-detail-error', message);
            return;
        }
        closeTodoDetail();
        refreshTodoSection();
    } catch (error) {
        showTodoDetailError('todo-detail-error', '저장에 실패했습니다.');
    } finally {
        saveBtn.disabled = false;
    }
});
