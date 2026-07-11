const selectedIds = new Set();

function toggleSelect(btn) {
    const card = btn.closest('.todo-card');
    const id = btn.dataset.id;
    if (selectedIds.has(id)) {
        selectedIds.delete(id);
        btn.classList.remove('todo-card__select--selected');
        card.classList.remove('todo-card--selected');
    } else {
        selectedIds.add(id);
        btn.classList.add('todo-card__select--selected');
        card.classList.add('todo-card--selected');
    }
    updateDeleteBtn();
}

function updateDeleteBtn() {
    const btn = document.getElementById('delete-btn');
    if (!btn) return;
    document.getElementById('selected-count').textContent = selectedIds.size;
    btn.style.display = selectedIds.size > 0 ? 'flex' : 'none';
}

function getSelectedIds() {
    return Array.from(selectedIds).join(',');
}

function clearSelection() {
    selectedIds.clear();
    document.querySelectorAll('.todo-card__select--selected').forEach(el => el.classList.remove('todo-card__select--selected'));
    document.querySelectorAll('.todo-card--selected').forEach(el => el.classList.remove('todo-card--selected'));
    updateDeleteBtn();
}

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
    if (!btn) return;
    btn.classList.remove('due-badge--none', 'due-badge--upcoming', 'due-badge--today', 'due-badge--overdue');
    if (dateStr) {
        const [y, m, d] = dateStr.split('-');
        btn.textContent = `📅 ${y}/${parseInt(m)}/${parseInt(d)}`;
        btn.classList.add('due-badge--upcoming');
    } else {
        btn.textContent = '📅 기한 추가';
        btn.classList.add('due-badge--none');
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
