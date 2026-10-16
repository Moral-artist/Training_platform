import request from "./request";
export async function getPlayAuthorization(lessonId) {
  return (await request.post(`/api/lessons/${lessonId}/play`)).data;
}
export async function getCatalog() {
  return (await request.get("/api/lessons/catalog")).data;
}
export async function getLesson(id) {
  return (await request.get(`/api/lessons/${id}/detail`)).data;
}
export async function deleteSystem(systemId) {
  return (await request.delete(`/api/lessons/systems_delete/${systemId}`))
}
// 只获取专业列表，不获取课程
export async function getSystems() {
  const res = await request.get("/api/lessons/systems");
  return res.data;
}

export async function deleteSystemLesson(systemId, lessonId) {
  return(await request.delete(`/api/lessons/systems/${systemId}/lessons/${lessonId}`)).data
}

// 按专业 ID 获取课程，后端分页
export async function getSystemLessons(
  systemId,
  currentPage = 1,
  pageSize = 10
) {
  const res = await request.get(
    `/api/lessons/majors/${systemId}/lessonlist`,
    {
      params: {
        current_page: currentPage,
        page_size: pageSize
      }
    }
  );
  return res.data;
}