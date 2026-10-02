
<template>
  <div class="home-page">

    <!-- ================= 左侧菜单 ================= -->
    <aside class="sidebar">

      <!-- Logo -->
      <div class="logo-area">
        <div class="logo-icon">
          ⚡
        </div>
        <div class="logo-text">
          <div class="logo-title">TRAINING</div>
          <div class="logo-subtitle">培训管理系统</div>
        </div>
      </div>

      <!-- 菜单 -->
      <nav class="menu">

        <div
          class="menu-item active"
          @click="goPage('home')"
        >
          <span class="menu-icon">⌂</span>
          <span>首页</span>
        </div>

        <div
          class="menu-item"
          @click="goPage('training')"
        >
          <span class="menu-icon">▣</span>
          <span>培训</span>
        </div>

        <div
          class="menu-item"
          @click="goPage('exam')"
        >
          <span class="menu-icon">✓</span>
          <span>考试</span>
        </div>

        <div
          class="menu-item"
          @click="goPage('materials')"
        >
          <span class="menu-icon">▤</span>
          <span>培训资料</span>
        </div>

        <div
          class="menu-item"
          @click="goPage('plan')"
        >
          <span class="menu-icon">◫</span>
          <span>培训计划</span>
        </div>

        <div
          class="menu-item"
          @click="goPage('results')"
        >
          <span class="menu-icon">▥</span>
          <span>成绩</span>
        </div>

      </nav>

      <!-- 底部设置 -->
      <div class="sidebar-bottom">
        <div class="menu-item">
          <span class="menu-icon">⚙</span>
          <span>设置</span>
        </div>
      </div>

    </aside>


    <!-- ================= 右侧主体 ================= -->
    <main class="main-content">

      <!-- 顶部 -->
      <header class="top-header">

        <div>
          <h1>首页</h1>
          <p>欢迎回来，开始今天的培训学习</p>
        </div>

        <div class="header-right">

          <!-- 通知 -->
          <div class="header-icon">
            🔔
            <span class="notification-dot"></span>
          </div>

          <!-- 用户 -->
          <div class="user-info">
            <div class="avatar">
              张
            </div>

            <div class="user-text">
              <div class="user-name">张三</div>
              <div class="user-role">值班员</div>
            </div>

            <span class="arrow">⌄</span>
          </div>

        </div>

      </header>


      <!-- ================= 欢迎卡片 ================= -->
      <section class="welcome-card">

        <div class="welcome-content">

          <div class="welcome-title">
            <span>👋</span>
            你好，张三
          </div>

          <div class="welcome-desc">
            今天也继续完成培训任务吧
          </div>

          <button
            class="primary-btn"
            @click="startTraining"
          >
            开始学习
            <span>→</span>
          </button>

        </div>

        <!-- 装饰 -->
        <div class="welcome-decoration">
          <div class="circle circle-1"></div>
          <div class="circle circle-2"></div>
          <div class="circle circle-3"></div>

          <div class="decoration-icon">
            🎓
          </div>
        </div>

      </section>


      <!-- ================= 数据概览 ================= -->
      <section class="section">

        <div class="section-title">
          <h2>学习概览</h2>
          <span>本月</span>
        </div>

        <div class="stats-grid">

          <!-- 培训 -->
          <div class="stat-card">

            <div class="stat-icon blue">
              📚
            </div>

            <div class="stat-info">
              <div class="stat-label">
                培训课程
              </div>

              <div class="stat-number">
                12
                <span>门</span>
              </div>

              <div class="stat-bottom">
                <span class="up">↑ 3</span>
                <span>较上月</span>
              </div>
            </div>

          </div>


          <!-- 完成 -->
          <div class="stat-card">

            <div class="stat-icon green">
              ✓
            </div>

            <div class="stat-info">
              <div class="stat-label">
                已完成
              </div>

              <div class="stat-number">
                8
                <span>门</span>
              </div>

              <div class="stat-bottom">
                <span class="up">↑ 2</span>
                <span>较上月</span>
              </div>
            </div>

          </div>


          <!-- 考试 -->
          <div class="stat-card">

            <div class="stat-icon purple">
              📝
            </div>

            <div class="stat-info">
              <div class="stat-label">
                参加考试
              </div>

              <div class="stat-number">
                5
                <span>次</span>
              </div>

              <div class="stat-bottom">
                <span class="up">↑ 1</span>
                <span>较上月</span>
              </div>
            </div>

          </div>


          <!-- 成绩 -->
          <div class="stat-card">

            <div class="stat-icon orange">
              ★
            </div>

            <div class="stat-info">
              <div class="stat-label">
                平均成绩
              </div>

              <div class="stat-number">
                92
                <span>分</span>
              </div>

              <div class="stat-bottom">
                <span class="up">↑ 5%</span>
                <span>较上月</span>
              </div>
            </div>

          </div>

        </div>

      </section>


      <!-- ================= 中间区域 ================= -->
      <section class="content-grid">


        <!-- ================= 我的培训 ================= -->
        <div class="panel training-panel">

          <div class="panel-header">

            <div>
              <h2>我的培训</h2>
              <p>当前需要完成的培训任务</p>
            </div>

            <button
              class="more-btn"
              @click="viewAllTraining"
            >
              查看全部 →
            </button>

          </div>


          <div class="training-list">

            <div
              class="training-item"
              v-for="item in trainingList"
              :key="item.id"
            >

              <div
                class="course-icon"
                :class="item.type"
              >
                {{ item.icon }}
              </div>

              <div class="course-info">

                <div class="course-name">
                  {{ item.name }}
                </div>

                <div class="course-meta">
                  {{ item.typeName }}
                  <span>·</span>
                  {{ item.duration }}
                </div>

                <div class="progress-area">

                  <div class="progress-bg">
                    <div
                      class="progress-bar"
                      :style="{ width: item.progress + '%' }"
                    ></div>
                  </div>

                  <span>
                    {{ item.progress }}%
                  </span>

                </div>

              </div>

              <button
                class="course-btn"
                @click="continueCourse(item)"
              >
                {{ item.progress === 0 ? '开始' : '继续' }}
              </button>

            </div>

          </div>

        </div>


        <!-- ================= 培训计划 ================= -->
        <div class="panel plan-panel">

          <div class="panel-header">

            <div>
              <h2>培训计划</h2>
              <p>近期培训安排</p>
            </div>

            <button
              class="more-btn"
              @click="viewPlan"
            >
              全部 →
            </button>

          </div>


          <div class="calendar">

            <div
              v-for="day in calendar"
              :key="day.date"
              class="calendar-day"
              :class="{ today: day.today }"
            >

              <div class="day-week">
                {{ day.week }}
              </div>

              <div class="day-number">
                {{ day.date }}
              </div>

            </div>

          </div>


          <div class="plan-list">

            <div
              class="plan-item"
              v-for="plan in plans"
              :key="plan.id"
            >

              <div class="plan-date">
                <strong>{{ plan.day }}</strong>
                <span>{{ plan.month }}</span>
              </div>

              <div class="plan-line"></div>

              <div class="plan-info">

                <div class="plan-name">
                  {{ plan.name }}
                </div>

                <div class="plan-time">
                  {{ plan.time }}
                </div>

              </div>

              <span
                class="plan-status"
                :class="plan.statusClass"
              >
                {{ plan.status }}
              </span>

            </div>

          </div>

        </div>

      </section>


      <!-- ================= 底部区域 ================= -->
      <section class="bottom-grid">


        <!-- 最近考试 -->
        <div class="panel">

          <div class="panel-header">

            <div>
              <h2>最近考试</h2>
              <p>考试成绩记录</p>
            </div>

            <button
              class="more-btn"
              @click="viewExam"
            >
              查看全部 →
            </button>

          </div>


          <div class="exam-list">

            <div
              v-for="exam in exams"
              :key="exam.id"
              class="exam-item"
            >

              <div class="exam-icon">
                📝
              </div>

              <div class="exam-info">

                <div class="exam-name">
                  {{ exam.name }}
                </div>

                <div class="exam-date">
                  {{ exam.date }}
                </div>

              </div>

              <div class="exam-score">
                <strong>{{ exam.score }}</strong>
                <span>分</span>
              </div>

            </div>

          </div>

        </div>


        <!-- 学习进度 -->
        <div class="panel progress-panel">

          <div class="panel-header">

            <div>
              <h2>我的学习进度</h2>
              <p>本月整体完成情况</p>
            </div>

          </div>


          <div class="progress-content">

            <div class="progress-circle">

              <div class="circle-inner">
                <strong>72%</strong>
                <span>完成率</span>
              </div>

            </div>


            <div class="progress-details">

              <div class="detail-row">
                <span>
                  <i class="dot blue-dot"></i>
                  培训课程
                </span>

                <strong>8 / 12</strong>
              </div>

              <div class="detail-row">
                <span>
                  <i class="dot green-dot"></i>
                  考试
                </span>

                <strong>5 / 6</strong>
              </div>

              <div class="detail-row">
                <span>
                  <i class="dot purple-dot"></i>
                  学习资料
                </span>

                <strong>18 / 25</strong>
              </div>

            </div>

          </div>

        </div>

      </section>


      <!-- ================= 页脚 ================= -->
      <footer>
        © 2026 培训管理系统 · Training Management System
      </footer>

    </main>

  </div>
</template>


<script setup>
import { ref } from 'vue'


/* ================= 培训数据 ================= */

const trainingList = ref([
  {
    id: 1,
    name: '数据中心基础知识',
    type: 'blue',
    typeName: '专业知识',
    duration: '45分钟',
    progress: 80,
    icon: '📘'
  },
  {
    id: 2,
    name: 'FM值班岗位职责',
    type: 'green',
    typeName: '岗位培训',
    duration: '30分钟',
    progress: 60,
    icon: '👨‍🔧'
  },
  {
    id: 3,
    name: '安全生产与红线',
    type: 'orange',
    typeName: '安全培训',
    duration: '35分钟',
    progress: 20,
    icon: '⚠'
  },
  {
    id: 4,
    name: 'HVAC系统基础',
    type: 'purple',
    typeName: '专业知识',
    duration: '50分钟',
    progress: 0,
    icon: '❄'
  }
])


/* ================= 培训计划 ================= */

const plans = ref([
  {
    id: 1,
    day: '18',
    month: '9月',
    name: 'HVAC系统基础培训',
    time: '09:00 - 10:00',
    status: '待学习',
    statusClass: 'waiting'
  },
  {
    id: 2,
    day: '20',
    month: '9月',
    name: '安全生产规则培训',
    time: '14:00 - 15:00',
    status: '待学习',
    statusClass: 'waiting'
  },
  {
    id: 3,
    day: '23',
    month: '9月',
    name: 'FM岗位能力考试',
    time: '10:00 - 11:00',
    status: '考试',
    statusClass: 'exam'
  }
])


/* ================= 日历 ================= */

const calendar = ref([
  {
    week: '一',
    date: 15,
    today: false
  },
  {
    week: '二',
    date: 16,
    today: false
  },
  {
    week: '三',
    date: 17,
    today: false
  },
  {
    week: '四',
    date: 18,
    today: true
  },
  {
    week: '五',
    date: 19,
    today: false
  },
  {
    week: '六',
    date: 20,
    today: false
  },
  {
    week: '日',
    date: 21,
    today: false
  }
])


/* ================= 考试 ================= */

const exams = ref([
  {
    id: 1,
    name: '数据中心基础知识考试',
    date: '2026-09-16',
    score: 95
  },
  {
    id: 2,
    name: 'FM岗位职责考试',
    date: '2026-09-12',
    score: 92
  },
  {
    id: 3,
    name: '安全生产培训考试',
    date: '2026-09-08',
    score: 89
  }
])


/* ================= 操作 ================= */

const startTraining = () => {
  console.log('开始学习')
}

const continueCourse = (item) => {
  console.log('继续课程:', item.name)
}

const viewAllTraining = () => {
  console.log('查看全部培训')
}

const viewPlan = () => {
  console.log('查看培训计划')
}

const viewExam = () => {
  console.log('查看考试')
}

const goPage = (page) => {
  console.log('跳转页面:', page)
}
</script>


<style scoped>

/* =====================================================
   基础
===================================================== */

* {
  box-sizing: border-box;
}

.home-page {
  min-height: 100vh;

  background:
    radial-gradient(
      circle at 90% 5%,
      rgba(80, 170, 255, 0.18),
      transparent 30%
    ),
    linear-gradient(
      135deg,
      #edf6ff 0%,
      #f5f9ff 45%,
      #e8f3ff 100%
    );

  display: flex;

  color: #26364a;

  font-family:
    "Microsoft YaHei",
    "PingFang SC",
    Arial,
    sans-serif;
}


/* =====================================================
   左侧菜单
===================================================== */

.sidebar {
  width: 230px;

  min-height: 100vh;

  background:
    linear-gradient(
      180deg,
      #1f67f2 0%,
      #2869e9 50%,
      #1959d7 100%
    );

  color: white;

  display: flex;

  flex-direction: column;

  padding: 24px 16px;

  box-shadow:
    8px 0 30px rgba(44, 102, 190, 0.15);
}


/* Logo */

.logo-area {
  display: flex;

  align-items: center;

  padding: 8px 10px 32px;
}

.logo-icon {
  width: 44px;
  height: 44px;

  border-radius: 13px;

  background: rgba(255, 255, 255, 0.18);

  display: flex;

  align-items: center;
  justify-content: center;

  font-size: 23px;

  margin-right: 10px;
}

.logo-title {
  font-size: 15px;

  font-weight: 700;

  letter-spacing: 1px;
}

.logo-subtitle {
  font-size: 12px;

  opacity: 0.75;

  margin-top: 3px;
}


/* 菜单 */

.menu {
  display: flex;

  flex-direction: column;

  gap: 8px;
}

.menu-item {
  height: 50px;

  padding: 0 18px;

  border-radius: 12px;

  display: flex;

  align-items: center;

  gap: 14px;

  cursor: pointer;

  font-size: 14px;

  transition: all 0.2s;
}

.menu-item:hover {
  background: rgba(255, 255, 255, 0.12);
}

.menu-item.active {
  background: white;

  color: #2165eb;

  box-shadow:
    0 8px 20px rgba(0, 45, 150, 0.15);
}

.menu-icon {
  width: 22px;

  text-align: center;

  font-size: 19px;
}

.sidebar-bottom {
  margin-top: auto;
}


/* =====================================================
   主体
===================================================== */

.main-content {
  flex: 1;

  min-width: 0;

  padding: 30px 38px;

  overflow: auto;
}


/* =====================================================
   顶部
===================================================== */

.top-header {
  display: flex;

  align-items: center;

  justify-content: space-between;

  margin-bottom: 25px;
}

.top-header h1 {
  margin: 0;

  font-size: 27px;

  font-weight: 700;

  color: #1d2e43;
}

.top-header p {
  margin: 7px 0 0;

  color: #8492a6;

  font-size: 13px;
}

.header-right {
  display: flex;

  align-items: center;

  gap: 24px;
}

.header-icon {
  width: 42px;
  height: 42px;

  background: white;

  border-radius: 12px;

  display: flex;

  align-items: center;
  justify-content: center;

  position: relative;

  box-shadow:
    0 5px 18px rgba(45, 91, 150, 0.07);

  cursor: pointer;
}

.notification-dot {
  width: 7px;
  height: 7px;

  background: #ff5d69;

  border-radius: 50%;

  position: absolute;

  top: 8px;
  right: 9px;
}

.user-info {
  display: flex;

  align-items: center;

  gap: 10px;

  cursor: pointer;
}

.avatar {
  width: 42px;
  height: 42px;

  border-radius: 50%;

  background:
    linear-gradient(
      135deg,
      #55a9ff,
      #2467ed
    );

  color: white;

  display: flex;

  align-items: center;
  justify-content: center;

  font-weight: 700;
}

.user-name {
  font-size: 14px;

  font-weight: 600;

  color: #29394e;
}

.user-role {
  margin-top: 3px;

  font-size: 11px;

  color: #8b99aa;
}

.arrow {
  color: #8c9aaa;

  margin-left: 4px;
}


/* =====================================================
   欢迎卡片
===================================================== */

.welcome-card {
  height: 190px;

  background:
    linear-gradient(
      110deg,
      #2268ef,
      #3789f7 65%,
      #65b1ff
    );

  border-radius: 20px;

  position: relative;

  overflow: hidden;

  box-shadow:
    0 14px 35px rgba(36, 105, 225, 0.2);

  margin-bottom: 28px;
}

.welcome-content {
  position: relative;

  z-index: 3;

  padding: 32px 38px;
}

.welcome-title {
  color: white;

  font-size: 25px;

  font-weight: 700;
}

.welcome-title span {
  margin-right: 8px;
}

.welcome-desc {
  color: rgba(255, 255, 255, 0.82);

  font-size: 14px;

  margin-top: 9px;
}

.primary-btn {
  margin-top: 22px;

  border: none;

  background: white;

  color: #2367ed;

  padding: 11px 20px;

  border-radius: 10px;

  font-size: 13px;

  font-weight: 600;

  cursor: pointer;

  box-shadow:
    0 5px 15px rgba(0, 40, 130, 0.15);

  transition: all 0.2s;
}

.primary-btn:hover {
  transform: translateY(-2px);
}

.primary-btn span {
  margin-left: 10px;
}


/* 欢迎卡片装饰 */

.welcome-decoration {
  position: absolute;

  right: 80px;
  top: -70px;

  width: 360px;
  height: 360px;
}

.circle {
  position: absolute;

  border-radius: 50%;

  border: 1px solid rgba(255, 255, 255, 0.25);
}

.circle-1 {
  width: 350px;
  height: 350px;
}

.circle-2 {
  width: 260px;
  height: 260px;

  top: 45px;
  left: 45px;
}

.circle-3 {
  width: 170px;
  height: 170px;

  top: 90px;
  left: 90px;
}

.decoration-icon {
  position: absolute;

  top: 130px;
  left: 140px;

  font-size: 60px;

  opacity: 0.9;
}


/* =====================================================
   Section
===================================================== */

.section {
  margin-bottom: 28px;
}

.section-title {
  display: flex;

  align-items: center;

  justify-content: space-between;

  margin-bottom: 14px;
}

.section-title h2 {
  margin: 0;

  font-size: 18px;

  color: #25364b;
}

.section-title > span {
  background: white;

  padding: 7px 14px;

  border-radius: 8px;

  font-size: 12px;

  color: #7d8ca0;
}


/* =====================================================
   数据卡片
===================================================== */

.stats-grid {
  display: grid;

  grid-template-columns:
    repeat(4, 1fr);

  gap: 16px;
}

.stat-card {
  background: white;

  border-radius: 16px;

  padding: 20px;

  display: flex;

  align-items: center;

  gap: 15px;

  box-shadow:
    0 7px 25px rgba(52, 90, 130, 0.07);

  border: 1px solid rgba(218, 229, 242, 0.6);

  transition: all 0.2s;
}

.stat-card:hover {
  transform: translateY(-3px);

  box-shadow:
    0 12px 30px rgba(52, 90, 130, 0.11);
}

.stat-icon {
  width: 52px;
  height: 52px;

  flex-shrink: 0;

  border-radius: 14px;

  display: flex;

  align-items: center;
  justify-content: center;

  font-size: 23px;
}

.stat-icon.blue {
  background: #e8f2ff;
}

.stat-icon.green {
  background: #e9f9f0;
}

.stat-icon.purple {
  background: #f1ecff;
}

.stat-icon.orange {
  background: #fff3e7;
}

.stat-label {
  color: #8491a3;

  font-size: 12px;
}

.stat-number {
  font-size: 25px;

  font-weight: 700;

  color: #26384e;

  margin-top: 3px;
}

.stat-number span {
  font-size: 11px;

  color: #8a98aa;

  font-weight: 400;
}

.stat-bottom {
  font-size: 10px;

  color: #a0aaba;

  margin-top: 3px;
}

.up {
  color: #36b779;

  margin-right: 5px;

  font-weight: 600;
}


/* =====================================================
   中间区域
===================================================== */

.content-grid {
  display: grid;

  grid-template-columns:
    1.45fr 1fr;

  gap: 20px;

  margin-bottom: 20px;
}

.panel {
  background: white;

  border-radius: 18px;

  padding: 22px;

  box-shadow:
    0 7px 25px rgba(52, 90, 130, 0.07);

  border: 1px solid rgba(218, 229, 242, 0.6);
}

.panel-header {
  display: flex;

  justify-content: space-between;

  align-items: center;

  margin-bottom: 18px;
}

.panel-header h2 {
  margin: 0;

  font-size: 17px;

  color: #26374c;
}

.panel-header p {
  margin: 5px 0 0;

  font-size: 11px;

  color: #9aa6b5;
}

.more-btn {
  border: none;

  background: none;

  color: #3276ee;

  font-size: 11px;

  cursor: pointer;
}


/* =====================================================
   培训列表
===================================================== */

.training-list {
  display: flex;

  flex-direction: column;

  gap: 12px;
}

.training-item {
  display: flex;

  align-items: center;

  gap: 13px;

  padding: 10px 8px;

  border-radius: 12px;

  transition: background 0.2s;
}

.training-item:hover {
  background: #f6faff;
}

.course-icon {
  width: 44px;
  height: 44px;

  border-radius: 12px;

  display: flex;

  align-items: center;
  justify-content: center;

  font-size: 19px;

  flex-shrink: 0;
}

.course-icon.blue {
  background: #eaf3ff;
}

.course-icon.green {
  background: #eaf9f1;
}

.course-icon.orange {
  background: #fff2e5;
}

.course-icon.purple {
  background: #f1edff;
}

.course-info {
  flex: 1;

  min-width: 0;
}

.course-name {
  font-size: 13px;

  font-weight: 600;

  color: #34445a;

  white-space: nowrap;

  overflow: hidden;

  text-overflow: ellipsis;
}

.course-meta {
  font-size: 10px;

  color: #9ba6b4;

  margin-top: 4px;
}

.course-meta span {
  margin: 0 4px;
}

.progress-area {
  display: flex;

  align-items: center;

  gap: 8px;

  margin-top: 7px;
}

.progress-bg {
  height: 5px;

  flex: 1;

  background: #edf1f6;

  border-radius: 10px;

  overflow: hidden;
}

.progress-bar {
  height: 100%;

  background:
    linear-gradient(
      90deg,
      #3c80f3,
      #61a8ff
    );

  border-radius: 10px;
}

.progress-area > span {
  font-size: 9px;

  color: #7e8c9e;

  width: 27px;
}

.course-btn {
  border: 1px solid #dbe8fb;

  background: #f5f9ff;

  color: #3474e9;

  border-radius: 8px;

  padding: 7px 13px;

  font-size: 10px;

  cursor: pointer;
}

.course-btn:hover {
  background: #eaf3ff;
}


/* =====================================================
   日历
===================================================== */

.calendar {
  display: grid;

  grid-template-columns:
    repeat(7, 1fr);

  gap: 5px;

  margin-bottom: 18px;
}

.calendar-day {
  text-align: center;

  padding: 7px 0;

  border-radius: 10px;
}

.day-week {
  color: #a0aaba;

  font-size: 9px;
}

.day-number {
  color: #45556a;

  font-size: 12px;

  font-weight: 600;

  margin-top: 5px;
}

.calendar-day.today {
  background: #eaf3ff;
}

.calendar-day.today .day-week,
.calendar-day.today .day-number {
  color: #2870eb;
}


/* =====================================================
   培训计划
===================================================== */

.plan-list {
  display: flex;

  flex-direction: column;

  gap: 12px;
}

.plan-item {
  display: flex;

  align-items: center;

  min-height: 48px;
}

.plan-date {
  width: 38px;

  text-align: center;
}

.plan-date strong {
  display: block;

  font-size: 16px;

  color: #2c6eea;
}

.plan-date span {
  display: block;

  font-size: 9px;

  color: #a1acb9;
}

.plan-line {
  width: 1px;

  height: 30px;

  background: #e4ebf4;

  margin: 0 13px;
}

.plan-info {
  flex: 1;
}

.plan-name {
  font-size: 11px;

  font-weight: 600;

  color: #46566a;
}

.plan-time {
  font-size: 9px;

  color: #a0aaba;

  margin-top: 4px;
}

.plan-status {
  padding: 4px 8px;

  border-radius: 6px;

  font-size: 9px;
}

.plan-status.waiting {
  background: #eef5ff;

  color: #4280e8;
}

.plan-status.exam {
  background: #fff3e6;

  color: #ed9941;
}


/* =====================================================
   底部区域
===================================================== */

.bottom-grid {
  display: grid;

  grid-template-columns:
    1fr 1fr;

  gap: 20px;
}


/* =====================================================
   考试
===================================================== */

.exam-list {
  display: flex;

  flex-direction: column;

  gap: 10px;
}

.exam-item {
  display: flex;

  align-items: center;

  padding: 9px;

  border-radius: 10px;

  background: #f8fbff;
}

.exam-icon {
  width: 38px;
  height: 38px;

  border-radius: 10px;

  background: #eaf3ff;

  display: flex;

  align-items: center;
  justify-content: center;

  font-size: 17px;

  margin-right: 11px;
}

.exam-info {
  flex: 1;
}

.exam-name {
  font-size: 11px;

  font-weight: 600;

  color: #46566a;
}

.exam-date {
  font-size: 9px;

  color: #9ca8b7;

  margin-top: 4px;
}

.exam-score {
  color: #2870ea;
}

.exam-score strong {
  font-size: 21px;
}

.exam-score span {
  font-size: 9px;

  margin-left: 2px;
}


/* =====================================================
   学习进度
===================================================== */

.progress-content {
  display: flex;

  align-items: center;

  justify-content: space-around;

  min-height: 150px;
}

.progress-circle {
  width: 125px;
  height: 125px;

  border-radius: 50%;

  background:
    conic-gradient(
      #3479ef 0deg 259deg,
      #e9f0f8 259deg 360deg
    );

  display: flex;

  align-items: center;
  justify-content: center;

  position: relative;
}

.progress-circle::before {
  content: "";

  position: absolute;

  width: 98px;
  height: 98px;

  background: white;

  border-radius: 50%;
}

.circle-inner {
  position: relative;

  z-index: 2;

  text-align: center;
}

.circle-inner strong {
  display: block;

  font-size: 23px;

  color: #2d70e7;
}

.circle-inner span {
  display: block;

  font-size: 9px;

  color: #9aa7b7;

  margin-top: 3px;
}

.progress-details {
  width: 180px;
}

.detail-row {
  display: flex;

  align-items: center;

  justify-content: space-between;

  padding: 9px 0;

  border-bottom: 1px solid #f0f3f7;

  font-size: 10px;

  color: #69788a;
}

.detail-row strong {
  color: #46576a;

  font-size: 11px;
}

.dot {
  width: 7px;
  height: 7px;

  border-radius: 50%;

  display: inline-block;

  margin-right: 7px;
}

.blue-dot {
  background: #3980ef;
}

.green-dot {
  background: #45c98a;
}

.purple-dot {
  background: #9170ed;
}


/* =====================================================
   Footer
===================================================== */

footer {
  text-align: center;

  color: #a3afbd;

  font-size: 10px;

  padding: 25px 0 5px;
}


/* =====================================================
   响应式
===================================================== */

@media (max-width: 1200px) {

  .sidebar {
    width: 200px;
  }

  .main-content {
    padding: 25px;
  }

  .stats-grid {
    grid-template-columns:
      repeat(2, 1fr);
  }

}


@media (max-width: 900px) {

  .sidebar {
    width: 72px;

    padding: 20px 10px;
  }

  .logo-text,
  .menu-item span:last-child {
    display: none;
  }

  .logo-area {
    justify-content: center;
    padding-bottom: 25px;
  }

  .logo-icon {
    margin: 0;
  }

  .menu-item {
    justify-content: center;

    padding: 0;
  }

  .content-grid,
  .bottom-grid {
    grid-template-columns: 1fr;
  }

}


@media (max-width: 650px) {

  .main-content {
    padding: 18px;
  }

  .top-header {
    align-items: flex-start;
  }

  .header-right {
    gap: 8px;
  }

  .user-text,
  .arrow {
    display: none;
  }

  .welcome-decoration {
    opacity: 0.35;

    right: -80px;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }

  .welcome-card {
    height: 175px;
  }

}

</style>