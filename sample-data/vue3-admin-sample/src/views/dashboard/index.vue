<template>
  <BaseTable />
</template>

<script setup lang="ts">
import BaseTable from '../../components/base/BaseTable.vue'
import { useUser } from '../../composables/useUser'

// 页面只负责组织视图，业务逻辑抽离到 composables。
useUser()
</script>

