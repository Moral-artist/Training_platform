// 上传和状态查询统一使用现有会话与 CSRF。
import request from './request'
export async function getVideoStatus(assetId) {
  return (await request.get(`/api/lessons_video/${assetId}/status`)).data
}
