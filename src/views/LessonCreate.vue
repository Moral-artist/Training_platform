<script setup>
  import {
    computed,
    nextTick,
    onMounted,
    onBeforeUnmount,
    reactive,
    ref,
    watch,
  } from "vue";
  import { useRoute, useRouter, onBeforeRouteLeave } from "vue-router";
  import request from "../api/request";
  import { getSystems, getLesson } from "../api/lessons";
  import { fingerprintFile, transferFile } from "../api/upload";
  import { auth } from "../stores/auth";
  import { t } from "../i18n";
  import { useTask } from "../composables/useTask";
  import { notify } from "../stores/notices";
  import PageState from "../components/PageState.vue";
  const route = useRoute(),
    router = useRouter(),
    editing = computed(() => !!route.params.lessonId);
  const draftKey = `training-draft:${auth.user.account_id}:${route.params.lessonId || "create"}`;
  let cached;
  try {
    cached = JSON.parse(localStorage.getItem(draftKey) || "null");
  } catch {
    localStorage.removeItem(draftKey);
  }
  const form = reactive({
    system_id: 0,
    lesson_name: "",
    description: "",
    video_asset_id: "",
    revision: 1,
    request_id: crypto.randomUUID(),
    ...(cached?.form || {}),
  });
  const upload = reactive({
    asset_id: "",
    content_hash: "",
    status: "",
    ...(cached?.upload || {}),
  });
  const maxUploadBytes = ref(8 * 1024 ** 3);
  const existingAsset = ref("");
  const file = ref(null),
    systems = ref([]),
    stage = ref(""),
    progress = ref(0),
    initialized = ref(false);
  const { busy, error, reference, run } = useTask();
  let controller,
    timer,
    alive = true;
  function persist() {
    if (initialized.value)
      localStorage.setItem(
        draftKey,
        JSON.stringify({ form: { ...form }, upload: { ...upload } }),
      );
  }
  watch([form, upload], persist, { deep: true });
  async function load() {
    await run(async () => {
      systems.value = await getSystems();
      const { data: limits } = await request.get("/api/uploads/config");
      maxUploadBytes.value = limits.max_upload_bytes || maxUploadBytes.value;
      if (editing.value) {
        const lesson = await getLesson(route.params.lessonId);
        if (!lesson.can_manage) throw { response: { status: 403 } };
        existingAsset.value = lesson.video_asset_id;
        if (!cached)
          Object.assign(form, {
            system_id: lesson.system_id,
            lesson_name: lesson.lesson_name,
            description: lesson.description,
            video_asset_id: lesson.video_asset_id,
            revision: lesson.revision,
          });
      }
      initialized.value = true;
      if (upload.asset_id) await poll();
    });
  }
  function choose(event) {
    file.value = event.target.files[0] || null;
  }
  async function poll() {
    clearTimeout(timer);
    try {
      const { data } = await request.get(
        `/api/lessons_video/${upload.asset_id}/status`,
      );
      if (!alive) return;
      upload.status = data.status;
      if (["uploaded", "processing"].includes(data.status))
        timer = setTimeout(poll, 5000);
    } catch (err) {
      if (!alive) return;
      error.value = `HTTP_${err.response?.status || 502}`;
      if (![401, 403, 404].includes(err.response?.status))
        timer = setTimeout(poll, 10000);
    }
  }
  async function submit() {
    await run(async () => {
      if (!form.system_id || !form.lesson_name.trim() || !form.description.trim())
        throw new Error("UI:HTTP_422");
      controller = new AbortController();
      if (file.value) {
        if (
          !["video/mp4", "video/webm"].includes(file.value.type) ||
          file.value.size <= 0 ||
          file.value.size > maxUploadBytes.value
        )
          throw new Error("UI:invalidFile");
        stage.value = "hashing";
        progress.value = 0;
        const hash = await fingerprintFile(
          file.value,
          (value) => {
            progress.value = value;
          },
          controller.signal,
        );
        if (upload.content_hash && upload.content_hash !== hash)
          throw new Error("UI:fileMismatch");
        const { data: info } = await request.post(
          "/api/uploads/start",
          {
            filename: file.value.name,
            size: file.value.size,
            content_type: file.value.type,
            content_hash: hash,
          },
          { signal: controller.signal },
        );
        Object.assign(upload, {
          asset_id: info.asset_id,
          content_hash: hash,
          status: info.status,
        });
        persist();
        if (info.status === "pending_upload") {
          stage.value = "uploading";
          progress.value = 0;
          const result = await transferFile(
            file.value,
            info,
            (value) => {
              progress.value = value;
            },
            controller.signal,
          );
          upload.status = result.status;
        } else notify("reused", "success");
        if (upload.status === "failed") {
          stage.value = "";
          await poll();
          return;
        }
        form.video_asset_id = upload.asset_id;
      } else if (upload.asset_id) {
        const { data: info } = await request.get(
          `/api/uploads/${upload.asset_id}`,
        );
        if (info.status === "pending_upload") throw new Error("UI:fileMismatch");
        if (info.status === "failed") throw new Error("UI:failed");
        form.video_asset_id = upload.asset_id;
      }
      if (!form.video_asset_id) throw new Error("UI:invalidFile");
      stage.value = "binding";
      persist();
      const body = {
        system_id: Number(form.system_id),
        lesson_name: form.lesson_name.trim(),
        description: form.description.trim(),
        video_asset_id: form.video_asset_id,
      };
      const { data } = editing.value
        ? await request.put(`/api/lessons/${route.params.lessonId}`, {
            ...body,
            revision: form.revision,
          })
        : await request.post("/api/lessons/lessonsubmit", {
            ...body,
            request_id: form.request_id,
          });
      if (!alive) return;
      // 收到创建结果后才清除草稿；响应丢失时同一 request_id 安全复用结果。
      initialized.value = false;
      localStorage.removeItem(draftKey);
      notify("saved", "success");
      /* await router.replace(`/lessons/${data.lesson_id}/detail`); */
      await router.push(`/lessons/create`)
    });
    stage.value = "";
  }
  function pause() {
    controller?.abort();
    persist();
  }
  async function discard() {
    await run(async () => {
      if (upload.asset_id) {
        const { data } = await request.get(`/api/uploads/${upload.asset_id}`);
        if (data.status === "pending_upload")
          await request.delete(`/api/uploads/${upload.asset_id}`);
      }
      // uploaded/ready 资产可能已绑定课程，仅解除本地草稿引用，绝不删除共享资产。
      Object.assign(upload, { asset_id: "", content_hash: "", status: "" });
      file.value = null;
      progress.value = 0;
      if (!editing.value) {
        form.video_asset_id = "";
        form.request_id = crypto.randomUUID();
      }
      if (editing.value) form.video_asset_id = existingAsset.value;
      initialized.value = false;
      localStorage.removeItem(draftKey);
      await nextTick();
      initialized.value = true;
    });
  }
  async function reloadCourse() {
    await run(async () => {
      const lesson = await getLesson(route.params.lessonId);
      existingAsset.value = lesson.video_asset_id;
      Object.assign(form, {
        system_id: lesson.system_id,
        lesson_name: lesson.lesson_name,
        description: lesson.description,
        video_asset_id: lesson.video_asset_id,
        revision: lesson.revision,
      });
      persist();
    });
  }
  async function retry() {
    await run(async () => {
      await request.post(`/api/lessons_video/${upload.asset_id}/retry`);
      await poll();
    });
  }
  onMounted(load);
  onBeforeRouteLeave(() => {
    pause();
  });
  onBeforeUnmount(() => {
    alive = false;
    pause();
    clearTimeout(timer);
  });
</script>
<template>
  <PageState
    :busy="busy && !initialized"
    :error="!initialized ? error : ''"
    :reference="reference"
    @retry="load"
  />
  <form v-if="initialized" class="card form" @submit.prevent="submit">
    <p>{{ t(editing ? "replaceHint" : "uploadHint") }}</p>
    <p class="hint">
      {{ t("fileSizeLimit") }}:
      {{ (maxUploadBytes / 1024 ** 3).toFixed(1) }} GiB
    </p>
    <p v-if="upload.asset_id" class="notice">{{ t("resumeHint") }}</p>
    <fieldset :disabled="busy" style="border: 0; padding: 0; margin: 0">
      <label class="field"
        ><span>{{ t("systemName") }}</span
        ><select v-model.number="form.system_id" required>
          <option :value="0" disabled>—</option>
          <option v-for="s in systems" :key="s.system_id" :value="s.system_id">
            {{ s.system_name }}
          </option>
        </select></label
      >
      <label class="field"
        ><span>{{ t("lessonName") }}</span
        ><input v-model="form.lesson_name" required maxlength="200"
      /></label>
      <label class="field"
        ><span>{{ t("description") }}</span
        ><textarea
          v-model="form.description"
          required
          maxlength="10000"
        ></textarea>
      </label>
      <label class="field"
        ><span>{{ t("selectVideo") }}</span
        ><input
          :key="upload.content_hash"
          type="file"
          accept="video/mp4,video/webm"
          @change="choose"
      /></label>
    </fieldset>
    <div v-if="stage" class="notice">
      <span><span class="spinner"></span>{{ t(stage) }} {{ progress }}%</span>
    </div>
    <progress v-if="stage" :value="progress" max="100"></progress>
    <p v-if="upload.status">{{ t("status") }}: {{ t(upload.status) }}</p>
    <PageState :error="error" :reference="reference" @retry="submit" />
    <button
      v-if="editing && error === 'HTTP_409'"
      type="button"
      class="secondary"
      :disabled="busy"
      @click="reloadCourse"
    >
      {{ t("reload") }}
    </button>
    <div class="actions">
      <button :disabled="busy">
        {{ t(editing ? "save" : "uploadSubmit") }}</button
      ><button
        v-if="busy && stage"
        type="button"
        class="secondary"
        @click="pause"
      >
        {{ t("pause") }}
      </button>
      <button
        v-if="upload.asset_id && !busy"
        type="button"
        class="secondary"
        @click="discard"
      >
        {{ t("discard") }}</button
      ><button
        v-if="upload.status === 'failed'"
        type="button"
        :disabled="busy"
        @click="retry"
      >
        {{ t("retry") }}
      </button>
    </div>
  </form>
</template>
