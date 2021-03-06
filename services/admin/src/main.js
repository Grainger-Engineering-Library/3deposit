import Vue from "vue";
import App from "./App";
import router from "./router/index";
import PaperDashboard from "./plugins/paperDashboard";
import "vue-notifyjs/themes/default.css";
import BootstrapVue from 'bootstrap-vue';
import ElementUI from 'element-ui';


Vue.use(BootstrapVue)
Vue.use(ElementUI)
Vue.use(PaperDashboard);
Vue.config.devtools = true;

/* eslint-disable no-new */
new Vue({
  router,
  render: h => h(App)
}).$mount("#app");
