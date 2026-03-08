// Faculty Logic

let currentUser = null;
let timetableData = [];

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    // Only proceed if authenticated
    if (!API.isAuthenticated()) {
        window.location.href = '../login.html';
        return;
    }
    loadData();
});

async function loadData() {
    try {
        currentUser = await API.getCurrentUser();
        if (!currentUser) {
            API.logout();
            return;
        }

        // Hide login modal since user is legit
        document.getElementById('login-modal').classList.add('hidden');
        updateUI();

        const fetchedData = await API.get('/timetables/');
        if (fetchedData && fetchedData.length > 0 && fetchedData[0].slots) {
            myClasses = fetchedData[0].slots.map(s => ({
                day: s.day_of_week,
                time: s.start_time.substring(0, 5),
                subject: s.course_name || s.subject || 'Course',
                faculty: s.faculty_name || s.faculty || 'Faculty',
                room: s.room_name || s.room || 'Room'
            }));

            // Optionally filter for the current faculty here if backend didn't
            if (currentUser.full_name) {
                myClasses = myClasses.filter(c => c.faculty === currentUser.full_name || c.faculty === currentUser.username);
            }
        } else {
            myClasses = [];
        }
    } catch (error) {
        console.error("Error loading faculty data:", error);
    }
}

function updateUI() {
    // Update Sidebar Profile
    document.getElementById('current-user-name').innerText = currentUser.full_name || currentUser.username;

    // Calculate Stats - To be refined when real timetable API is wired
    const currentLoad = 0; // Replace with length from API data

    document.getElementById('stat-current-load').innerText = currentLoad;
    document.getElementById('stat-max-load').innerText = 18;

    const loadPercent = Math.min((currentLoad / (currentUser.max || 18)) * 100, 100);
    document.getElementById('load-bar').style.width = `${loadPercent}%`;
    document.getElementById('load-bar').className = `h-full rounded-full ${currentLoad > (currentUser.max || 18) ? 'bg-red-500' : 'bg-blue-500'}`;

    // Render Timetable
    renderMySchedule(myClasses);

    // update Next Class view
    // (Simple logic: just show a random one or first one for demo)
    if (myClasses.length > 0) {
        const next = myClasses[0]; // Just showing first found
        document.getElementById('next-class-container').innerHTML = `
            <p class="text-xl font-bold mt-1 text-text-main">${next.subject}</p>
            <div class="flex items-center gap-2 mt-2 text-sm text-text-muted font-semibold">
                <i class="fa-regular fa-clock text-fuchsia-400"></i> ${next.day} @ ${next.time}
            </div>
            <div class="flex items-center gap-2 mt-1 text-sm text-text-muted font-semibold">
                <i class="fa-solid fa-location-dot text-fuchsia-400"></i> ${next.room}
            </div>
        `;
    } else {
        document.getElementById('next-class-container').innerHTML = `
            <p class="text-xl font-bold mt-1 text-text-muted">No classes assigned</p>
        `;
    }
}

function renderMySchedule(classes) {
    const times = ["09:00", "10:00", "11:00", "12:00", "01:00", "02:00", "03:00"];
    const days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"];
    const container = document.getElementById('faculty-timetable-body');

    container.innerHTML = times.map(time => `
        <div class="grid grid-cols-6 border-b border-border-color min-h-[100px]">
            <div class="p-4 border-r border-border-color text-xs font-bold text-text-muted flex items-center justify-center bg-main">
                ${time}
            </div>
            ${days.map(day => {
        const cls = classes.find(c => c.day === day && c.time === time);
        return `
                    <div class="p-2 border-r border-border-color relative group transition-colors hover:bg-main">
                        ${cls ? `
                            <div class="bg-fuchsia-500/10 border border-fuchsia-500/20 p-3 rounded-xl h-full shadow-sm hover:shadow-lg hover:shadow-fuchsia-900/20 transition-all cursor-pointer group-hover:-translate-y-1">
                                <p class="text-[10px] font-black text-fuchsia-400 uppercase tracking-tight neon-text">Lecture</p>
                                <p class="text-xs font-extra-bold text-text-main leading-tight mt-1 mb-2">${cls.subject}</p>
                                <div class="flex items-center gap-1 text-[10px] font-bold text-text-muted bg-main inline-block px-2 py-1 rounded-md border border-border-color">
                                    <i class="fa-solid fa-location-dot text-fuchsia-400"></i> ${cls.room}
                                </div>
                            </div>
                        ` : ''}
                    </div>
                `;
    }).join('')}
        </div>
    `).join('');
}

// Navigation
function showPage(pageId) {
    document.querySelectorAll('.page-content').forEach(p => p.classList.add('hidden'));
    document.querySelectorAll('.sidebar-item').forEach(b => b.classList.remove('active'));
    document.getElementById(`page-${pageId}`).classList.remove('hidden');
    document.getElementById(`btn-${pageId}`).classList.add('active');
}

function printSchedule() {
    window.print();
}

// Modal generic toggler
async function toggleModal(modalId, show = true) {
    const modal = document.getElementById(modalId);
    if (!modal) return;
    if (show) {
        modal.classList.remove('hidden');
        if (modalId === 'modal-leave') {
            await populateLeaveDropdowns();
        }
    } else {
        modal.classList.add('hidden');
    }
}

// Populate Leave Dropdowns for Modal
async function populateLeaveDropdowns() {
    try {
        const semResp = await API.get('/semesters/');
        const sel = document.getElementById('leave-semester');
        if (sel) {
            sel.innerHTML = '<option value="">Select Semester</option>' +
                semResp.map(s => `<option value="${s.id}">Sem ${s.semester_number} (${s.year})</option>`).join('');
        }
    } catch (e) {
        console.error('Failed to fetch semesters', e);
    }
}

// Submit Leave Request
async function submitLeaveRequest() {
    const leave_type = document.getElementById('leave-type').value;
    const start_date = document.getElementById('leave-start').value;
    const end_date = document.getElementById('leave-end').value;
    const semester_id = document.getElementById('leave-semester').value;
    const reason = document.getElementById('leave-reason').value;

    if (!start_date || !end_date) return alert('Please select a start and end date');

    try {
        await API.post('/faculty-leaves/', {
            faculty_id: parseInt(currentUser.id),
            timetable_id: null,
            leave_type,
            start_date,
            end_date,
            semester_id: semester_id ? parseInt(semester_id) : null,
            reason
        });

        toggleModal('modal-leave', false);
        alert('Leave request submitted successfully');
    } catch (error) {
        console.error('Error submitting leave request:', error);
        alert(error.message || 'Error submitting leave request');
    }
}
