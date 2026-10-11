import request from './request'

// 获取某课程的考试
export async function getExams(lessonId) {
  return (
    await request.get('/api/exams/getExams', {
      params: {
        lesson_id: lessonId
      }
    })
  ).data
}

// 开始一次考试
/* export async function startExam(examId) {
  return (
    await request.post('/api/attemptExam', {
      exam_id: examId
    })
  ).data
}

// 提交考试
export async function submitExam(data) {
  return (
    await request.post('/api/submitAttempt', data)
  ).data
} */

// 创建考试
export async function createExam(data) {
  const response = await request.post("/api/exams/createExams", data);
  return response.data;
}

// 删除考试
// 你的后端 exam_id: int 是 query 参数，不是 JSON body
export async function deleteExam(examId) {
  return (
    await request.post(
      '/api/exams/deleteExams',
      null,
      {
        params: {
          exam_id: examId
        }
      }
    )
  ).data
}

export async function getLessonExams(lessonId) {
  const res = await request.get("/api/exams/getExams", {
    params: { lesson_id: lessonId }
  });
  return res.data;
}

// 开始考试
export async function startExam(lessonId, examId, planId) {
  const res = await request.post("/api/exams/attemptExam", {
    lesson_id: Number(lessonId),
    exam_id: Number(examId),
    plan_id: Number(planId)
  });
  return res.data;
}

// 提交考试
export async function submitExam(attemptId, answers) {
  const res = await request.post("/api/exams/submitAttempt", {
    attempt_id: Number(attemptId),
    questions: answers
  });
  return res.data;
}

// 查询历史考试记录
export async function getMyAttempts() {
  const res = await request.get("/api/exams/my_attempts");
  return res.data;
}