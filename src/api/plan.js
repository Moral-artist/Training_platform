import request from './request'

export async function getPresetPlanList() {
  return await request.get('/api/plan/preset_planlist')
}

export async function addTemplatePlan(data) {
  return await request.post('/api/plan/add_template_plan', data)
}

export async function addCustomPlan(data) {
  return await request.post('/api/plan/add_custom_plan', data)
}