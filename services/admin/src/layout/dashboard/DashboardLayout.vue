<template>
  <div class="wrapper">
    <side-bar>
      <template slot="links">
        <sidebar-link to="/admin/dashboard" name="Dashboard" icon="ti-dashboard"/>
        <sidebar-link to="/admin/profile" name="User Profile" icon="ti-id-badge"/>
        <sidebar-link to="/admin/deposits" name="Deposits" icon="ti-package"/>
        <sidebar-link to="/admin/gallery-builder" name="Gallery" icon="ti-gallery"/>
        <sidebar-link v-show="current_user.role === 'admin'" to="/admin/actions" name="Actions" icon="ti-control-play"/>
        <sidebar-link v-show="current_user.role === 'admin'" to="/admin/forms" name="Forms" icon="ti-pencil-alt"/>
        <sidebar-link v-show="current_user.role === 'admin'" to="/admin/services" name="Services" icon="ti-panel"/>
        <sidebar-link v-show="current_user.role === 'admin'" to="/admin/users" name="Users" icon="fa fa-users"/>
        <sidebar-link v-show="current_user.role === 'admin'" to="/admin/settings" name="Settings" icon="ti-settings"/>
      </template>
      <mobile-menu>
        <li class="nav-item">
          <a class="nav-link">
            <i class="ti-panel"></i>
            <p>Profile</p>
          </a>
        </li>
        <drop-down class="nav-item"
                   title="Notifications"
                   title-classes="nav-link"
                   icon="ti-bell">
          <!-- <a class="dropdown-item">Notification 1</a>
          <a class="dropdown-item">Notification 2</a>
          <a class="dropdown-item">Notification 3</a>
          <a class="dropdown-item">Notification 4</a>
          <a class="dropdown-item">Another notification</a> -->
        </drop-down>
        <li class="nav-item">
          <a class="nav-link">
            <i class="ti-settings"></i>
            <p>Settings</p>
          </a>
        </li>
        <li class="divider"></li>
      </mobile-menu>
    </side-bar>
    <div class="main-panel">
      <top-navbar :current_user="current_user"></top-navbar>

      <dashboard-content :current_user="current_user" @click.native="toggleSidebar">

      </dashboard-content>

      <content-footer></content-footer>
    </div>
  </div>
</template>
<style lang="scss">
</style>
<script>
import axios from 'axios';

import TopNavbar from "./TopNavbar.vue";
import ContentFooter from "./ContentFooter.vue";
import DashboardContent from "./Content.vue";
import MobileMenu from "./MobileMenu";

export default {
  components: {
    TopNavbar,
    ContentFooter,
    DashboardContent,
    MobileMenu
  },
  data() {
    return {
      current_user: {}
    }
  },
  created() {
    axios.get('../api/user')
    .then(response => {
      if (response.status == 200) {
        this.current_user = response.data.current_user;
      }
    },
    error => {
      if (error) {
        window.location.href = '../api/login';
        }
    })
  },
  methods: {
    toggleSidebar() {
      if (this.$sidebar.showSidebar) {
        this.$sidebar.displaySidebar(false);
      }
    }
  }
};
</script>
