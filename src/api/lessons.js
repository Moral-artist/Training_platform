import request from './request'


/* =========================
   四个专业
========================= */

export const majors = [

  {
    code: 'electrical',
    name: '电气',
    english: 'Electrical',
    short: 'E',

    // 用来匹配数据库 systems.system_name
    aliases: [
      'electrical',
      'electric',
      'electrical system',
      '电气'
    ]
  },

  {
    code: 'hvac',
    name: '暖通',
    english: 'HVAC',
    short: 'H',

    aliases: [
      'hvac',
      'heating ventilation air conditioning',
      '暖通'
    ]
  },

  {
    code: 'elv',
    name: '弱电',
    english: 'ELV',
    short: 'ELV',

    aliases: [
      'elv',
      'weak current',
      'low voltage',
      '弱电'
    ]
  },

  {
    code: 'fire',
    name: '消防',
    english: 'Fire Protection',
    short: 'F',

    aliases: [
      'fire',
      'fire protection',
      'fire fighting',
      '消防'
    ]
  }

]


/* =========================
   获取当前登录用户
========================= */

export async function getCurrentUser() {

  const response = await request.get(
    '/api/user/user_info'
  )

  return response.data
}


/* =========================
   获取所有专业
========================= */

export async function getSystems() {

  const response = await request.get(
    '/api/lessons/systems'
  )

  return response.data
}


/* =========================
   根据专业找到 system_id
========================= */

export function findSystemForMajor(
  systems,
  major
) {

  if (!major) {
    return null
  }


  const result = systems.find(
    (system) => {

      const systemName =
        String(
          system.system_name || ''
        )
          .trim()
          .toLowerCase()


      return major.aliases.some(
        (alias) => {

          return (
            systemName ===
            alias.toLowerCase()
          )

        }
      )

    }
  )


  return result || null
}


/* =========================
   获取当前专业全部课程
========================= */

export async function getAuthorizedLessons(
  systemId
) {

  /*
    第一次请求第一页

    对应后端：

    GET
    /api/lessons/majors/{system_id}/lessonlist
  */

  const firstResponse =
    await request.get(

      `/api/lessons/majors/${systemId}/lessonlist`,

      {
        params: {

          current_page: 1,

          page_size: 10

        }
      }

    )


  const firstData =
    firstResponse.data


  /*
    后端返回：

    {
      total_lessons,
      total_pages,
      current_page,
      lessonlist: []
    }
  */

  const allLessons = [
    ...(firstData.lessonlist || [])
  ]


  const totalPages =
    firstData.total_pages || 1


  /*
    如果只有一页，
    直接返回
  */

  if (totalPages <= 1) {

    return allLessons

  }


  /*
    如果有多页：

    page 2
    page 3
    page 4
    ...

    全部请求回来
  */

  for (
    let page = 2;
    page <= totalPages;
    page++
  ) {

    const response =
      await request.get(

        `/api/lessons/majors/${systemId}/lessonlist`,

        {
          params: {

            current_page: page,

            page_size: 10

          }
        }

      )


    const pageLessons =
      response.data.lessonlist || []


    allLessons.push(
      ...pageLessons
    )

  }


  return allLessons
}


/* =========================
   根据 lesson_id 找课程
========================= */

export async function getAuthorizedLessonById(
  systemId,
  lessonId
) {

  const response = await request.get(`/api/lessons/${lessonId}/detail`)
  return response.data
}


/* =========================
   视频播放接口
   先预留
========================= */

export async function getPlayAuthorization(
  lessonId
) {

  const response =
    await request.post(

      `/api/lessons/${lessonId}/play`

    )


  return response.data
}

export function getMajor(code) {
  return majors.find(item => item.code === code) || null
}

export async function loadAuthorizedMajorLessons(code) {
  const major = getMajor(code)
  if (!major) throw new Error('没有找到这个专业。')
  const systems = await getSystems()
  const system = findSystemForMajor(systems, major)
  if (!system) throw new Error('数据库还没有配置这个专业。')
  const lessons = await getAuthorizedLessons(system.system_id)
  return lessons.map(item => ({ ...item, id: item.lesson_id, title: item.lesson_name }))
}
