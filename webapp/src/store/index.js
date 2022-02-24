import { createStore } from 'vuex'

const store = createStore({
  state() {
    return {
      list: []
    }
  },
  mutations: {
    set_list(state, list) {
      state.list = list
    }
  }
})

export default store
