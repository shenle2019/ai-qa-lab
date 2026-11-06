/**
 * One project selection for the whole workspace.
 *
 * Every page used to keep its own key (`aiqa.modules.project`, `aiqa.ui.project` …),
 * so switching to a project on one page left the others on an empty default.
 * Pages now read/write the shared key and only fall back to their old key once.
 */
export const PROJECT_KEY = 'aiqa.project'

export function readProjectId(legacyKey) {
  const shared = Number(window.localStorage.getItem(PROJECT_KEY) || 0)
  if (shared > 0) return shared
  const legacy = legacyKey ? Number(window.localStorage.getItem(legacyKey) || 0) : 0
  return legacy > 0 ? legacy : 0
}

export function saveProjectId(projectId, legacyKey) {
  if (!projectId) return
  window.localStorage.setItem(PROJECT_KEY, String(projectId))
  if (legacyKey) window.localStorage.setItem(legacyKey, String(projectId))
}

export function pickProject(projects, legacyKey) {
  if (!projects || !projects.length) return null
  const saved = readProjectId(legacyKey)
  return projects.find((item) => item.id === saved) || projects[0]
}

/**
 * Same as pickProject, but when nothing is remembered yet it prefers the project
 * with the most test cases instead of whatever the API returned first — otherwise
 * modules/members land on an empty demo project and look broken.
 */
export async function pickProjectSmart(projects, legacyKey, fetchCases) {
  if (!projects || !projects.length) return null
  const saved = readProjectId(legacyKey)
  const hit = projects.find((item) => item.id === saved)
  if (hit) return hit
  try {
    const cases = await fetchCases()
    const tally = new Map()
    for (const item of cases || []) {
      tally.set(item.project_id, (tally.get(item.project_id) || 0) + 1)
    }
    const ranked = [...projects].sort(
      (a, b) => (tally.get(b.id) || 0) - (tally.get(a.id) || 0) || a.id - b.id,
    )
    return ranked[0]
  } catch {
    return projects[0]
  }
}
