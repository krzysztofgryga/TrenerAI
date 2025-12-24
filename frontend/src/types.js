// Typy dla aplikacji TrenerAI

/**
 * @typedef {Object} Client
 * @property {string} id
 * @property {string} name
 * @property {number} age
 * @property {number} weight
 * @property {string} goal
 * @property {string} notes
 * @property {string} createdAt
 * @property {ProgressEntry[]} progress
 */

/**
 * @typedef {Object} ProgressEntry
 * @property {string} id
 * @property {string} date
 * @property {number} weight
 * @property {number} [bodyFat]
 * @property {number} [waist]
 * @property {string} [notes]
 */

/**
 * @typedef {Object} CalendarEvent
 * @property {string} id
 * @property {string} clientId
 * @property {string} clientName
 * @property {string} title
 * @property {string} date
 * @property {string} time
 * @property {'workout' | 'consultation' | 'checkup'} type
 * @property {boolean} remindCoach
 * @property {boolean} remindClient
 */

/**
 * @typedef {Object} SavedWorkout
 * @property {string} id
 * @property {string} title
 * @property {string} content
 * @property {string} date
 * @property {string} [color]
 */

export const AppView = {
    CHAT: 'chat',
    SAVED: 'saved',
    CLIENTS: 'clients',
    CALENDAR: 'calendar',
    SETTINGS: 'settings'
};
