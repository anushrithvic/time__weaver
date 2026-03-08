// ==============================
// admin-pages.js — CRUD logic for new admin dashboard pages
// Uses same API_BASE from app.js
// ==============================

// ---- ELECTIVE GROUPS ----
let electiveGroupsData = [];

async function loadElectiveGroups() {
    try {
        const response = await fetch(`${API_BASE}/elective-groups/`);
        electiveGroupsData = await response.json();
        renderElectiveGroups();
    } catch (error) {
        console.error('Error loading elective groups:', error);
    }
}

function renderElectiveGroups() {
    const tbody = document.getElementById('elective-groups-list');
    if (!tbody) return;
    if (!electiveGroupsData.length) {
        tbody.innerHTML = '<tr><td colspan="5" class="px-8 py-12 text-center text-text-muted italic">No elective groups found</td></tr>';
        return;
    }
    tbody.innerHTML = electiveGroupsData.map(eg => `
        <tr class="hover:bg-main transition-colors">
            <td class="px-8 py-4 text-text-muted text-sm">${eg.id}</td>
            <td class="px-8 py-4 text-text-main font-semibold">${eg.name || '-'}</td>
            <td class="px-8 py-4 text-text-muted text-sm">${eg.description || '-'}</td>
            <td class="px-8 py-4 text-text-muted text-sm">${(eg.departments || []).map(d => d.name || d.code).join(', ') || '-'}</td>
            <td class="px-8 py-4 text-center">
                <button onclick="deleteElectiveGroup(${eg.id})" class="text-red-400 hover:text-red-300 transition-colors">
                    <i class="fa-solid fa-trash"></i>
                </button>
            </td>
        </tr>
    `).join('');
}

async function saveElectiveGroup() {
    const name = document.getElementById('eg-name').value;
    const description = document.getElementById('eg-desc').value;
    if (!name) return alert('Please enter a group name');

    try {
        const response = await fetch(`${API_BASE}/elective-groups/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, description })
        });
        if (response.ok) {
            toggleModal('modal-elective-group', false);
            document.getElementById('eg-name').value = '';
            document.getElementById('eg-desc').value = '';
            loadElectiveGroups();
        } else {
            const data = await response.json();
            alert(data.detail || 'Failed to create elective group');
        }
    } catch (error) {
        console.error('Error saving elective group:', error);
        alert('Error saving elective group');
    }
}

async function deleteElectiveGroup(id) {
    if (!confirm('Delete this elective group?')) return;
    try {
        const response = await fetch(`${API_BASE}/elective-groups/${id}`, { method: 'DELETE' });
        if (response.ok) loadElectiveGroups();
    } catch (error) {
        console.error('Error deleting elective group:', error);
    }
}

// ---- TIME SLOTS ----
let timeSlotsData = [];

async function loadTimeSlots() {
    try {
        const filterDay = document.getElementById('ts-filter-day')?.value;
        let url = `${API_BASE}/time-slots/`;
        if (filterDay) url += `?day_of_week=${filterDay}`;
        const response = await fetch(url);
        timeSlotsData = await response.json();
        renderTimeSlots();
    } catch (error) {
        console.error('Error loading time slots:', error);
    }
}

function renderTimeSlots() {
    const tbody = document.getElementById('timeslots-list');
    if (!tbody) return;
    if (!timeSlotsData.length) {
        tbody.innerHTML = '<tr><td colspan="6" class="px-8 py-12 text-center text-text-muted italic">No time slots found</td></tr>';
        return;
    }
    tbody.innerHTML = timeSlotsData.map(ts => `
        <tr class="hover:bg-main transition-colors">
            <td class="px-8 py-4 text-text-main font-semibold">${ts.day_of_week}</td>
            <td class="px-8 py-4 text-text-muted text-sm">${ts.start_time}</td>
            <td class="px-8 py-4 text-text-muted text-sm">${ts.end_time}</td>
            <td class="px-8 py-4 text-text-muted text-sm">${ts.duration_minutes || '-'} min</td>
            <td class="px-8 py-4">
                <span class="px-3 py-1 rounded-full text-xs font-bold ${ts.is_break ? 'bg-amber-500/10 text-amber-400' : 'bg-green-500/10 text-green-400'}">
                    ${ts.is_break ? 'Break' : ts.slot_type || 'Regular'}
                </span>
            </td>
            <td class="px-8 py-4 text-center">
                <button onclick="deleteTimeSlot(${ts.id})" class="text-red-400 hover:text-red-300 transition-colors">
                    <i class="fa-solid fa-trash"></i>
                </button>
            </td>
        </tr>
    `).join('');
}

async function saveTimeSlot() {
    const day_of_week = document.getElementById('ts-day').value;
    const start_time = document.getElementById('ts-start').value;
    const end_time = document.getElementById('ts-end').value;
    const duration_minutes = parseInt(document.getElementById('ts-duration').value);
    const slot_type = document.getElementById('ts-type').value;
    const is_break = document.getElementById('ts-break').checked;

    if (!start_time || !end_time) return alert('Please fill start and end time');

    try {
        const response = await fetch(`${API_BASE}/time-slots/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ day_of_week, start_time, end_time, duration_minutes, slot_type, is_break })
        });
        if (response.ok) {
            toggleModal('modal-timeslot', false);
            document.getElementById('ts-start').value = '';
            document.getElementById('ts-end').value = '';
            loadTimeSlots();
        } else {
            const data = await response.json();
            alert(data.detail || 'Failed to create time slot');
        }
    } catch (error) {
        console.error('Error saving time slot:', error);
        alert('Error saving time slot');
    }
}

async function deleteTimeSlot(id) {
    if (!confirm('Delete this time slot?')) return;
    try {
        const response = await fetch(`${API_BASE}/time-slots/${id}`, { method: 'DELETE' });
        if (response.ok) loadTimeSlots();
    } catch (error) {
        console.error('Error deleting time slot:', error);
    }
}

// ---- CONSTRAINTS ----
let constraintsData = [];

async function loadConstraints() {
    try {
        const response = await fetch(`${API_BASE}/constraints/`);
        constraintsData = await response.json();
        renderConstraints();
    } catch (error) {
        console.error('Error loading constraints:', error);
    }
}

function renderConstraints() {
    const tbody = document.getElementById('constraints-list');
    if (!tbody) return;
    if (!constraintsData.length) {
        tbody.innerHTML = '<tr><td colspan="6" class="px-8 py-12 text-center text-text-muted italic">No constraints defined</td></tr>';
        return;
    }
    tbody.innerHTML = constraintsData.map(c => `
        <tr class="hover:bg-main transition-colors">
            <td class="px-8 py-4 text-text-main font-semibold">${c.name || '-'}</td>
            <td class="px-8 py-4 text-text-muted text-sm">${c.constraint_type || '-'}</td>
            <td class="px-8 py-4 text-text-muted text-sm">${c.category || '-'}</td>
            <td class="px-8 py-4 text-text-muted text-sm">${c.priority || '-'}</td>
            <td class="px-8 py-4">
                <span class="px-3 py-1 rounded-full text-xs font-bold ${c.is_hard ? 'bg-red-500/10 text-red-400' : 'bg-blue-500/10 text-blue-400'}">
                    ${c.is_hard ? 'Hard' : 'Soft'}
                </span>
            </td>
            <td class="px-8 py-4 text-center flex items-center justify-center gap-3">
                <button onclick="explainConstraint(${c.id})" class="text-blue-400 hover:text-blue-300 transition-colors" title="Explain">
                    <i class="fa-solid fa-circle-info"></i>
                </button>
                <button onclick="deleteConstraint(${c.id})" class="text-red-400 hover:text-red-300 transition-colors" title="Delete">
                    <i class="fa-solid fa-trash"></i>
                </button>
            </td>
        </tr>
    `).join('');
}

async function saveConstraint() {
    const name = document.getElementById('con-name').value;
    const constraint_type = document.getElementById('con-type').value;
    const category = document.getElementById('con-category').value;
    const rule_definition = document.getElementById('con-rule').value;
    const priority = parseInt(document.getElementById('con-priority').value);
    const weight = parseFloat(document.getElementById('con-weight').value);
    const is_hard = document.getElementById('con-hard').checked;

    if (!name) return alert('Please enter a constraint name');

    try {
        const response = await fetch(`${API_BASE}/constraints/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, constraint_type, category, rule_definition, priority, weight, is_hard })
        });
        if (response.ok) {
            toggleModal('modal-constraint', false);
            document.getElementById('con-name').value = '';
            document.getElementById('con-rule').value = '';
            loadConstraints();
        } else {
            const data = await response.json();
            alert(data.detail || 'Failed to create constraint');
        }
    } catch (error) {
        console.error('Error saving constraint:', error);
        alert('Error saving constraint');
    }
}

async function explainConstraint(id) {
    try {
        const response = await fetch(`${API_BASE}/constraints/${id}/explain`);
        if (response.ok) {
            const explanation = await response.json();
            alert(`Constraint Explanation:\n\n${explanation.explanation || JSON.stringify(explanation, null, 2)}`);
        } else {
            alert('Could not get explanation');
        }
    } catch (error) {
        console.error('Error explaining constraint:', error);
    }
}

async function deleteConstraint(id) {
    if (!confirm('Delete this constraint?')) return;
    try {
        const response = await fetch(`${API_BASE}/constraints/${id}`, { method: 'DELETE' });
        if (response.ok) loadConstraints();
    } catch (error) {
        console.error('Error deleting constraint:', error);
    }
}

// ---- FACULTY LEAVES ----
let leavesData = [];

async function loadLeaves() {
    try {
        const response = await fetch(`${API_BASE}/faculty-leaves/`);
        leavesData = await response.json();
        renderLeaves();
        updateLeaveStats();
        populateLeaveDropdowns();
    } catch (error) {
        console.error('Error loading leaves:', error);
    }
}

function updateLeaveStats() {
    const pending = leavesData.filter(l => l.status === 'PENDING').length;
    const approved = leavesData.filter(l => l.status === 'APPROVED').length;
    const rejected = leavesData.filter(l => l.status === 'REJECTED').length;
    const elPending = document.getElementById('stat-leaves-pending');
    const elApproved = document.getElementById('stat-leaves-approved');
    const elRejected = document.getElementById('stat-leaves-rejected');
    if (elPending) elPending.textContent = pending;
    if (elApproved) elApproved.textContent = approved;
    if (elRejected) elRejected.textContent = rejected;
}

async function populateLeaveDropdowns() {
    // Populate faculty dropdown
    try {
        const facultyResp = await fetch(`${API_BASE}/users/?role=faculty`);
        const facultyList = await facultyResp.json();
        const sel = document.getElementById('leave-faculty');
        if (sel) {
            sel.innerHTML = '<option value="">Select Faculty</option>' +
                facultyList.map(f => `<option value="${f.id}">${f.full_name || f.username}</option>`).join('');
        }
    } catch (e) { console.error(e); }

    // Populate timetable dropdown
    try {
        const ttResp = await fetch(`${API_BASE}/timetables/`);
        const ttList = await ttResp.json();
        const sel = document.getElementById('leave-timetable');
        if (sel) {
            sel.innerHTML = '<option value="">Select Timetable</option>' +
                ttList.map(t => `<option value="${t.id}">${t.name || 'Timetable #' + t.id}</option>`).join('');
        }
        // Also populate slot-locks timetable dropdown
        const lockSel = document.getElementById('lock-timetable-id');
        if (lockSel) {
            lockSel.innerHTML = '<option value="">Select Timetable</option>' +
                ttList.map(t => `<option value="${t.id}">${t.name || 'Timetable #' + t.id}</option>`).join('');
        }
    } catch (e) { console.error(e); }

    // Populate semester dropdown
    try {
        const semResp = await fetch(`${API_BASE}/semesters`);
        const semList = await semResp.json();
        const sel = document.getElementById('leave-semester');
        if (sel) {
            sel.innerHTML = '<option value="">Select Semester</option>' +
                semList.map(s => `<option value="${s.id}">Sem ${s.semester_number} (${s.year})</option>`).join('');
        }
    } catch (e) { console.error(e); }
}

function renderLeaves() {
    const tbody = document.getElementById('leaves-list');
    if (!tbody) return;
    if (!leavesData.length) {
        tbody.innerHTML = '<tr><td colspan="6" class="px-8 py-12 text-center text-text-muted italic">No leave requests</td></tr>';
        return;
    }
    const statusColors = {
        PENDING: 'bg-amber-500/10 text-amber-400',
        APPROVED: 'bg-green-500/10 text-green-400',
        REJECTED: 'bg-red-500/10 text-red-400',
        APPLIED: 'bg-blue-500/10 text-blue-400',
    };
    tbody.innerHTML = leavesData.map(l => `
        <tr class="hover:bg-main transition-colors">
            <td class="px-8 py-4 text-text-main font-semibold">${l.faculty_name || 'Faculty #' + l.faculty_id}</td>
            <td class="px-8 py-4 text-text-muted text-sm">${l.leave_type || '-'}</td>
            <td class="px-8 py-4 text-text-muted text-sm">${l.start_date ? new Date(l.start_date).toLocaleDateString() : '-'}</td>
            <td class="px-8 py-4 text-text-muted text-sm">${l.end_date ? new Date(l.end_date).toLocaleDateString() : '-'}</td>
            <td class="px-8 py-4">
                <span class="px-3 py-1 rounded-full text-xs font-bold ${statusColors[l.status] || 'bg-gray-500/10 text-gray-400'}">
                    ${l.status || 'Unknown'}
                </span>
            </td>
            <td class="px-8 py-4 text-center flex items-center justify-center gap-2">
                ${l.status === 'PENDING' ? `
                    <button onclick="approveLeave(${l.id})" class="text-green-400 hover:text-green-300 transition-colors" title="Approve">
                        <i class="fa-solid fa-check"></i>
                    </button>
                    <button onclick="rejectLeave(${l.id})" class="text-red-400 hover:text-red-300 transition-colors" title="Reject">
                        <i class="fa-solid fa-xmark"></i>
                    </button>
                ` : ''}
                ${l.status === 'APPROVED' ? `
                    <button onclick="applyLeave(${l.id})" class="text-blue-400 hover:text-blue-300 transition-colors" title="Apply to schedule">
                        <i class="fa-solid fa-calendar-check"></i>
                    </button>
                ` : ''}
                <button onclick="analyzeLeave(${l.id})" class="text-cyan-400 hover:text-cyan-300 transition-colors" title="Impact Analysis">
                    <i class="fa-solid fa-chart-line"></i>
                </button>
            </td>
        </tr>
    `).join('');
}

async function saveLeave() {
    const faculty_id = document.getElementById('leave-faculty').value;
    const timetable_id = document.getElementById('leave-timetable').value;
    const leave_type = document.getElementById('leave-type').value;
    const start_date = document.getElementById('leave-start').value;
    const end_date = document.getElementById('leave-end').value;
    const semester_id = document.getElementById('leave-semester').value;
    const reason = document.getElementById('leave-reason').value;

    if (!faculty_id || !start_date || !end_date) return alert('Please fill in required fields');

    try {
        const response = await fetch(`${API_BASE}/faculty-leaves/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                faculty_id: parseInt(faculty_id),
                timetable_id: timetable_id ? parseInt(timetable_id) : null,
                leave_type,
                start_date,
                end_date,
                semester_id: parseInt(semester_id),
                reason
            })
        });
        if (response.ok) {
            toggleModal('modal-leave', false);
            loadLeaves();
        } else {
            const data = await response.json();
            alert(data.detail || 'Failed to create leave request');
        }
    } catch (error) {
        console.error('Error saving leave:', error);
        alert('Error saving leave request');
    }
}

async function approveLeave(id) {
    if (!confirm('Approve this leave request?')) return;
    try {
        const response = await fetch(`${API_BASE}/faculty-leaves/${id}/approve`, { method: 'PATCH' });
        if (response.ok) loadLeaves();
        else alert('Failed to approve leave');
    } catch (error) { console.error(error); }
}

async function rejectLeave(id) {
    if (!confirm('Reject this leave request?')) return;
    try {
        const response = await fetch(`${API_BASE}/faculty-leaves/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: 'REJECTED' })
        });
        if (response.ok) loadLeaves();
        else alert('Failed to reject leave');
    } catch (error) { console.error(error); }
}

async function applyLeave(id) {
    if (!confirm('Apply this leave to the timetable schedule?')) return;
    try {
        const response = await fetch(`${API_BASE}/faculty-leaves/${id}/apply`, { method: 'PATCH' });
        if (response.ok) {
            alert('Leave applied to schedule successfully');
            loadLeaves();
        } else alert('Failed to apply leave');
    } catch (error) { console.error(error); }
}

async function analyzeLeave(id) {
    try {
        const response = await fetch(`${API_BASE}/faculty-leaves/analyze`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ leave_id: id })
        });
        if (response.ok) {
            const analysis = await response.json();
            alert(`Impact Analysis:\n\n${JSON.stringify(analysis, null, 2)}`);
        } else alert('Could not analyze impact');
    } catch (error) { console.error(error); }
}

// ---- SLOT LOCKS ----
async function loadLockedSlots() {
    const timetableId = document.getElementById('lock-timetable-id')?.value;
    if (!timetableId) return;
    try {
        const response = await fetch(`${API_BASE}/slot-locks/locked?timetable_id=${timetableId}`);
        const data = await response.json();
        renderLockedSlots(data);
    } catch (error) {
        console.error('Error loading locked slots:', error);
    }
}

function renderLockedSlots(slots) {
    const tbody = document.getElementById('locked-slots-list');
    if (!tbody) return;
    if (!slots || !slots.length) {
        tbody.innerHTML = '<tr><td colspan="6" class="px-8 py-12 text-center text-text-muted italic">No locked slots. Select a timetable above.</td></tr>';
        return;
    }
    tbody.innerHTML = slots.map(s => `
        <tr class="hover:bg-main transition-colors">
            <td class="px-8 py-4 text-text-main font-semibold">${s.slot_id || s.id}</td>
            <td class="px-8 py-4 text-text-muted text-sm">${s.day_of_week || '-'}</td>
            <td class="px-8 py-4 text-text-muted text-sm">${s.start_time || '-'} - ${s.end_time || '-'}</td>
            <td class="px-8 py-4 text-text-muted text-sm">${s.course_name || '-'}</td>
            <td class="px-8 py-4 text-text-muted text-sm">${s.room_name || '-'}</td>
            <td class="px-8 py-4 text-center">
                <span class="px-3 py-1 rounded-full text-xs font-bold bg-red-500/10 text-red-400">
                    <i class="fa-solid fa-lock mr-1"></i> Locked
                </span>
            </td>
        </tr>
    `).join('');
}

async function lockSlots() {
    const timetable_id = document.getElementById('lock-timetable-id')?.value;
    const slotIdsStr = document.getElementById('lock-slot-ids')?.value;
    if (!timetable_id || !slotIdsStr) return alert('Please select a timetable and enter slot IDs');

    const slot_ids = slotIdsStr.split(',').map(s => parseInt(s.trim())).filter(n => !isNaN(n));
    if (!slot_ids.length) return alert('Invalid slot IDs');

    try {
        const response = await fetch(`${API_BASE}/slot-locks/lock`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ timetable_id: parseInt(timetable_id), slot_ids })
        });
        if (response.ok) {
            document.getElementById('lock-slot-ids').value = '';
            loadLockedSlots();
            alert('Slots locked successfully');
        } else {
            const data = await response.json();
            alert(data.detail || 'Failed to lock slots');
        }
    } catch (error) {
        console.error('Error locking slots:', error);
    }
}

async function unlockSlots() {
    const timetable_id = document.getElementById('lock-timetable-id')?.value;
    const slotIdsStr = document.getElementById('lock-slot-ids')?.value;
    if (!timetable_id || !slotIdsStr) return alert('Please select a timetable and enter slot IDs');

    const slot_ids = slotIdsStr.split(',').map(s => parseInt(s.trim())).filter(n => !isNaN(n));
    if (!slot_ids.length) return alert('Invalid slot IDs');

    try {
        const response = await fetch(`${API_BASE}/slot-locks/unlock`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ timetable_id: parseInt(timetable_id), slot_ids })
        });
        if (response.ok) {
            document.getElementById('lock-slot-ids').value = '';
            loadLockedSlots();
            alert('Slots unlocked successfully');
        } else {
            const data = await response.json();
            alert(data.detail || 'Failed to unlock slots');
        }
    } catch (error) {
        console.error('Error unlocking slots:', error);
    }
}

// ---- USER MANAGEMENT ----
let usersData = [];

async function loadUsers() {
    try {
        const roleFilter = document.getElementById('user-filter-role')?.value;
        let url = `${API_BASE}/users/`;
        if (roleFilter) url += `?role=${roleFilter}`;
        const response = await fetch(url);
        usersData = await response.json();
        renderUsers();
    } catch (error) {
        console.error('Error loading users:', error);
    }
}

function renderUsers() {
    const tbody = document.getElementById('users-list');
    if (!tbody) return;
    if (!usersData.length) {
        tbody.innerHTML = '<tr><td colspan="6" class="px-8 py-12 text-center text-text-muted italic">No users found</td></tr>';
        return;
    }
    const roleColors = {
        admin: 'bg-red-500/10 text-red-400',
        faculty: 'bg-blue-500/10 text-blue-400',
        student: 'bg-cyan-500/10 text-cyan-400',
    };
    tbody.innerHTML = usersData.map(u => `
        <tr class="hover:bg-main transition-colors">
            <td class="px-8 py-4 text-text-main font-semibold">${u.username}</td>
            <td class="px-8 py-4 text-text-muted text-sm">${u.full_name || '-'}</td>
            <td class="px-8 py-4 text-text-muted text-sm">${u.email || '-'}</td>
            <td class="px-8 py-4">
                <span class="px-3 py-1 rounded-full text-xs font-bold ${roleColors[u.role] || 'bg-gray-500/10 text-gray-400'}">
                    ${u.role || '-'}
                </span>
            </td>
            <td class="px-8 py-4">
                <span class="px-3 py-1 rounded-full text-xs font-bold ${u.is_active ? 'bg-green-500/10 text-green-400' : 'bg-gray-500/10 text-gray-400'}">
                    ${u.is_active ? 'Active' : 'Inactive'}
                </span>
            </td>
            <td class="px-8 py-4 text-center flex items-center justify-center gap-3">
                <button onclick="deleteUser(${u.id})" class="text-red-400 hover:text-red-300 transition-colors" title="Delete">
                    <i class="fa-solid fa-trash"></i>
                </button>
            </td>
        </tr>
    `).join('');
}

async function saveUser() {
    const username = document.getElementById('user-username').value;
    const full_name = document.getElementById('user-fullname').value;
    const email = document.getElementById('user-email').value;
    const password = document.getElementById('user-password').value;
    const role = document.getElementById('user-role').value;

    if (!username || !password) return alert('Username and password are required');

    try {
        const response = await fetch(`${API_BASE}/users/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, full_name, email, password, role })
        });
        if (response.ok) {
            toggleModal('modal-user', false);
            document.getElementById('user-username').value = '';
            document.getElementById('user-fullname').value = '';
            document.getElementById('user-email').value = '';
            document.getElementById('user-password').value = '';
            loadUsers();
        } else {
            const data = await response.json();
            alert(data.detail || 'Failed to create user');
        }
    } catch (error) {
        console.error('Error saving user:', error);
        alert('Error creating user');
    }
}

async function deleteUser(id) {
    if (!confirm('Delete this user? This cannot be undone.')) return;
    try {
        const response = await fetch(`${API_BASE}/users/${id}`, { method: 'DELETE' });
        if (response.ok) loadUsers();
        else alert('Failed to delete user');
    } catch (error) {
        console.error('Error deleting user:', error);
    }
}

// ---- AUDIT LOGS ----
let auditLogsData = [];

async function loadAuditLogs() {
    try {
        const entity = document.getElementById('audit-filter-entity')?.value;
        const action = document.getElementById('audit-filter-action')?.value;
        const start = document.getElementById('audit-filter-start')?.value;
        const end = document.getElementById('audit-filter-end')?.value;

        let params = [];
        if (entity) params.push(`entity_type=${entity}`);
        if (action) params.push(`action=${action}`);
        if (start) params.push(`start_date=${start}`);
        if (end) params.push(`end_date=${end}`);

        let url = `${API_BASE}/audit-logs/`;
        if (params.length) url += '?' + params.join('&');

        const response = await fetch(url);
        auditLogsData = await response.json();
        renderAuditLogs();
    } catch (error) {
        console.error('Error loading audit logs:', error);
    }
}

function renderAuditLogs() {
    const tbody = document.getElementById('audit-logs-list');
    if (!tbody) return;
    if (!auditLogsData.length) {
        tbody.innerHTML = '<tr><td colspan="5" class="px-8 py-12 text-center text-text-muted italic">No audit logs found</td></tr>';
        return;
    }
    const actionColors = {
        create: 'bg-green-500/10 text-green-400',
        update: 'bg-blue-500/10 text-blue-400',
        delete: 'bg-red-500/10 text-red-400',
        login: 'bg-cyan-500/10 text-cyan-400',
    };
    tbody.innerHTML = auditLogsData.map(log => `
        <tr class="hover:bg-main transition-colors">
            <td class="px-8 py-4 text-text-muted text-sm">${log.created_at ? new Date(log.created_at).toLocaleString() : '-'}</td>
            <td class="px-8 py-4 text-text-main font-semibold">${log.user_name || log.username || 'System'}</td>
            <td class="px-8 py-4">
                <span class="px-3 py-1 rounded-full text-xs font-bold ${actionColors[log.action] || 'bg-gray-500/10 text-gray-400'}">
                    ${log.action || '-'}
                </span>
            </td>
            <td class="px-8 py-4 text-text-muted text-sm">${log.entity_type || '-'} ${log.entity_id ? '#' + log.entity_id : ''}</td>
            <td class="px-8 py-4 text-text-muted text-sm max-w-xs truncate">${log.details || log.description || '-'}</td>
        </tr>
    `).join('');
}

// ---- FACULTY PREFERENCES ----
let facultyPreferencesData = [];

async function loadFacultyPreferences() {
    try {
        const response = await fetch(`${API_BASE}/faculty-preferences/`);
        facultyPreferencesData = await response.json();
        renderFacultyPreferences();
        populatePreferenceDropdowns();
    } catch (error) {
        console.error('Error loading faculty preferences:', error);
    }
}

async function populatePreferenceDropdowns() {
    try {
        const facultyResp = await fetch(`${API_BASE}/users/?role=faculty`);
        const facultyList = await facultyResp.json();
        const selFac = document.getElementById('fp-faculty');
        if (selFac) {
            selFac.innerHTML = '<option value="">Select Faculty</option>' +
                facultyList.map(f => `<option value="${f.id}">${f.full_name || f.username}</option>`).join('');
        }
        const tsResp = await fetch(`${API_BASE}/time-slots/`);
        const tsList = await tsResp.json();
        const selTs = document.getElementById('fp-timeslot');
        if (selTs) {
            const arr = Array.isArray(tsList) ? tsList : tsList.data;
            selTs.innerHTML = '<option value="">Select Time Slot</option>' +
                (arr || []).map(t => `<option value="${t.id}">${t.day_of_week} ${t.start_time}-${t.end_time}</option>`).join('');
        }
    } catch (e) { console.error(e); }
}

function renderFacultyPreferences() {
    const tbody = document.getElementById('faculty-preferences-list');
    if (!tbody) return;
    if (!facultyPreferencesData.length) {
        tbody.innerHTML = '<tr><td colspan="6" class="px-8 py-12 text-center text-text-muted italic">No preferences found</td></tr>';
        return;
    }
    const levelColors = {
        PREFER: 'bg-green-500/10 text-green-400',
        AVOID: 'bg-amber-500/10 text-amber-400',
        MUST_HAVE: 'bg-blue-500/10 text-blue-400',
        CANNOT_HAVE: 'bg-red-500/10 text-red-400',
    };
    tbody.innerHTML = facultyPreferencesData.map(p => `
        <tr class="hover:bg-main transition-colors">
            <td class="px-8 py-4 text-text-main font-semibold">Faculty #${p.faculty_id}</td>
            <td class="px-8 py-4 text-text-muted text-sm">${p.day_of_week || 'Any'}</td>
            <td class="px-8 py-4 text-text-muted text-sm">${p.start_time || '-'} to ${p.end_time || '-'}</td>
            <td class="px-8 py-4">
                <span class="px-3 py-1 rounded-full text-xs font-bold ${levelColors[p.preference_level] || 'bg-gray-500/10 text-gray-400'}">
                    ${p.preference_level || '-'} (W: ${p.weight})
                </span>
            </td>
            <td class="px-8 py-4 text-text-muted text-sm">${p.semester_id ? 'Sem #' + p.semester_id : 'All'}</td>
            <td class="px-8 py-4 text-center">
                <button onclick="deleteFacultyPreference(${p.id})" class="text-red-400 hover:text-red-300 transition-colors">
                    <i class="fa-solid fa-trash"></i>
                </button>
            </td>
        </tr>
    `).join('');
}

async function saveFacultyPreference() {
    const faculty_id = document.getElementById('fp-faculty').value;
    const day_of_week = document.getElementById('fp-day').value;
    const time_slot_id = document.getElementById('fp-timeslot').value;
    const preference_type = document.getElementById('fp-type').value;

    if (!faculty_id || !time_slot_id) return alert('Please select a faculty member and time slot');

    try {
        const response = await fetch(`${API_BASE}/faculty-preferences/?faculty_id=${faculty_id}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                day_of_week: parseInt(day_of_week),
                time_slot_id: parseInt(time_slot_id),
                preference_type: preference_type
            })
        });
        if (response.ok) {
            toggleModal('modal-faculty-preference', false);
            loadFacultyPreferences();
        } else {
            const data = await response.json();
            alert(data.detail || 'Failed to create preference');
        }
    } catch (error) {
        console.error('Error saving preference:', error);
        alert('Error saving preference');
    }
}

async function deleteFacultyPreference(id) {
    if (!confirm('Delete this preference?')) return;
    try {
        const response = await fetch(`${API_BASE}/faculty-preferences/${id}`, { method: 'DELETE' });
        if (response.ok) loadFacultyPreferences();
    } catch (error) {
        console.error('Error deleting preference:', error);
    }
}

// ---- FACULTY COURSES ----
let facultyCoursesData = [];

async function loadFacultyCourses() {
    try {
        const response = await fetch(`${API_BASE}/faculty-courses/`);
        facultyCoursesData = await response.json();
        renderFacultyCourses();
        populateFacultyCourseDropdowns();
    } catch (error) {
        console.error('Error loading faculty courses:', error);
    }
}

async function populateFacultyCourseDropdowns() {
    try {
        // Faculty
        const facultyResp = await fetch(`${API_BASE}/users/?role=faculty`);
        const facultyList = await facultyResp.json();
        const selFac = document.getElementById('fc-faculty');
        if (selFac) {
            selFac.innerHTML = '<option value="">Select Faculty</option>' +
                facultyList.map(f => `<option value="${f.id}">${f.full_name || f.username}</option>`).join('');
        }
        // Courses
        const courseResp = await fetch(`${API_BASE}/courses/`);
        const courseList = await courseResp.json();
        const selCourse = document.getElementById('fc-course');
        if (selCourse) {
            selCourse.innerHTML = '<option value="">Select Course</option>' +
                courseList.map(c => `<option value="${c.id}">${c.name} (${c.code})</option>`).join('');
        }
        // Sections
        const secResp = await fetch(`${API_BASE}/sections/`);
        const secList = await secResp.json();
        const selSec = document.getElementById('fc-section');
        if (selSec) {
            selSec.innerHTML = '<option value="">Select Section (General assignment if none)</option>' +
                secList.map(s => `<option value="${s.id}">${s.name}</option>`).join('');
        }
        // Semesters
        const semResp = await fetch(`${API_BASE}/semesters/`);
        const semList = await semResp.json();
        const selSem = document.getElementById('fc-semester');
        if (selSem) {
            selSem.innerHTML = '<option value="">Select Semester</option>' +
                semList.map(s => `<option value="${s.id}">Sem ${s.semester_number} (${s.year})</option>`).join('');
        }
    } catch (e) { console.error(e); }
}

function renderFacultyCourses() {
    const tbody = document.getElementById('faculty-courses-list');
    if (!tbody) return;
    if (!facultyCoursesData.length) {
        tbody.innerHTML = '<tr><td colspan="7" class="px-8 py-12 text-center text-text-muted italic">No faculty course assignments found</td></tr>';
        return;
    }
    tbody.innerHTML = facultyCoursesData.map(fc => `
        <tr class="hover:bg-main transition-colors">
            <td class="px-8 py-4 text-text-main font-semibold">Faculty #${fc.faculty_id}</td>
            <td class="px-8 py-4 text-text-muted text-sm">Course #${fc.course_id}</td>
            <td class="px-8 py-4 text-text-muted text-sm">${fc.section_id ? 'Section #' + fc.section_id : 'All Sections'}</td>
            <td class="px-8 py-4 text-text-muted text-sm">Sem #${fc.semester_id}</td>
            <td class="px-8 py-4 text-text-muted text-sm">${fc.hours_assigned}</td>
            <td class="px-8 py-4">
                <span class="px-3 py-1 rounded-full text-xs font-bold ${fc.is_primary ? 'bg-blue-500/10 text-blue-400' : 'bg-gray-500/10 text-gray-400'}">
                    ${fc.is_primary ? 'Yes' : 'No'}
                </span>
            </td>
            <td class="px-8 py-4 text-center">
                <button onclick="deleteFacultyCourse(${fc.id})" class="text-red-400 hover:text-red-300 transition-colors">
                    <i class="fa-solid fa-trash"></i>
                </button>
            </td>
        </tr>
    `).join('');
}

async function saveFacultyCourse() {
    const faculty_id = document.getElementById('fc-faculty').value;
    const course_id = document.getElementById('fc-course').value;
    const section_id = document.getElementById('fc-section').value;
    const semester_id = document.getElementById('fc-semester').value;
    const is_primary = document.getElementById('fc-primary').checked;

    if (!faculty_id || !course_id || !semester_id) return alert('Faculty, Course, and Semester are required');

    try {
        const response = await fetch(`${API_BASE}/faculty-courses/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                faculty_id: parseInt(faculty_id),
                course_id: parseInt(course_id),
                section_id: section_id ? parseInt(section_id) : null,
                semester_id: parseInt(semester_id),
                is_primary
            })
        });
        if (response.ok) {
            toggleModal('modal-faculty-course', false);
            loadFacultyCourses();
        } else {
            const data = await response.json();
            alert(data.detail || 'Failed to assign course');
        }
    } catch (error) {
        console.error('Error assigning course:', error);
        alert('Error assigning course');
    }
}

async function deleteFacultyCourse(id) {
    if (!confirm('Delete this course assignment?')) return;
    try {
        const response = await fetch(`${API_BASE}/faculty-courses/${id}`, { method: 'DELETE' });
        if (response.ok) loadFacultyCourses();
    } catch (error) {
        console.error('Error deleting course assignment:', error);
    }
}

// ---- HOOK INTO showPage from app.js ----
// Override the existing showPage to also handle new pages
const _originalShowPage = typeof showPage === 'function' ? showPage : null;

function showPage(pageId) {
    // Hide all pages
    document.querySelectorAll('.page-content').forEach(p => p.classList.add('hidden'));

    // Show the target page
    const target = document.getElementById('page-' + pageId);
    if (target) target.classList.remove('hidden');

    // Update sidebar active state
    document.querySelectorAll('.sidebar-item').forEach(btn => btn.classList.remove('active'));
    const btn = document.getElementById('btn-' + pageId);
    if (btn) btn.classList.add('active');

    // Load data for the new pages
    switch (pageId) {
        case 'elective-groups': loadElectiveGroups(); break;
        case 'timeslots': loadTimeSlots(); break;
        case 'constraints': loadConstraints(); break;
        case 'faculty-leaves': loadLeaves(); break;
        case 'faculty-preferences': loadFacultyPreferences(); break;
        case 'faculty-courses': loadFacultyCourses(); break;
        case 'slot-locks': populateLeaveDropdowns(); loadLockedSlots(); break;
        case 'users': loadUsers(); break;
        case 'audit-logs': loadAuditLogs(); break;
        // Existing pages from app.js
        case 'overview': if (typeof updateStats === 'function') updateStats(); break;
        case 'faculty': if (typeof loadFaculty === 'function') loadFaculty(); break;
        case 'student': if (typeof loadStudents === 'function') loadStudents(); break;
        case 'rooms': if (typeof loadRooms === 'function') loadRooms(); break;
        case 'departments': if (typeof loadDepartments === 'function') loadDepartments(); break;
        case 'courses': if (typeof loadCourses === 'function') loadCourses(); break;
        case 'semesters': if (typeof loadSemesters === 'function') loadSemesters(); break;
        case 'sections': if (typeof loadSections === 'function') loadSections(); break;
        case 'conflicts': if (typeof renderConflicts === 'function') renderConflicts(); break;
        case 'institution': if (typeof loadRules === 'function') loadRules(); break;
        case 'timetable': if (typeof loadTimetable === 'function') loadTimetable(false); break;
    }
}
