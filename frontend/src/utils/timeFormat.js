/**
 * Converts total minutes to HH:MM format
 * @param {number|string} totalMinutes 
 * @returns {string} HH:MM
 */
export const minutesToHHMM = (totalMinutes) => {
    if (!totalMinutes || isNaN(totalMinutes)) return '00:00';
    const mins = parseInt(totalMinutes);
    const h = Math.floor(mins / 60);
    const m = mins % 60;
    return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}`;
};

/**
 * Converts HH:MM format to total minutes
 * @param {string} hhmm 
 * @returns {number} minutes
 */
export const hhmmToMinutes = (hhmm) => {
    if (!hhmm || typeof hhmm !== 'string') return 0;
    const [h, m] = hhmm.split(':').map(val => parseInt(val) || 0);
    return (h * 60) + m;
};

/**
 * Validates HH:MM format
 * @param {string} hhmm 
 * @returns {boolean}
 */
export const validateHHMM = (hhmm) => {
    const regex = /^([0-9]{1,2}):([0-5][0-9])$/;
    return regex.test(hhmm);
};
