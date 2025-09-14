module.exports = {
  apps: [
    {
      name: 'web-ui',
      script: 'web_ui.py',
      interpreter: 'python3',
      cwd: '/opt/media-pipeline',
      user: 'media-pipeline',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      env: {
        NODE_ENV: 'production',
        PORT: 8080
      },
      error_file: '/var/log/media-pipeline/web-ui-error.log',
      out_file: '/var/log/media-pipeline/web-ui-out.log',
      log_file: '/var/log/media-pipeline/web-ui.log',
      time: true
    },
    {
      name: 'pipeline-dashboard',
      script: 'web_ui.py',
      interpreter: 'python3',
      cwd: '/opt/media-pipeline',
      user: 'media-pipeline',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      env: {
        NODE_ENV: 'production',
        PORT: 8081
      },
      error_file: '/var/log/media-pipeline/pipeline-dashboard-error.log',
      out_file: '/var/log/media-pipeline/pipeline-dashboard-out.log',
      log_file: '/var/log/media-pipeline/pipeline-dashboard.log',
      time: true
    },
    {
      name: 'status-dashboard',
      script: 'web_status_dashboard.py',
      interpreter: 'python3',
      cwd: '/opt/media-pipeline',
      user: 'media-pipeline',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      env: {
        NODE_ENV: 'production',
        PORT: 8082
      },
      error_file: '/var/log/media-pipeline/status-dashboard-error.log',
      out_file: '/var/log/media-pipeline/status-dashboard-out.log',
      log_file: '/var/log/media-pipeline/status-dashboard.log',
      time: true
    },
    {
      name: 'config-interface',
      script: 'web_config_interface.py',
      interpreter: 'python3',
      cwd: '/opt/media-pipeline',
      user: 'media-pipeline',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      env: {
        NODE_ENV: 'production',
        PORT: 8083
      },
      error_file: '/var/log/media-pipeline/config-interface-error.log',
      out_file: '/var/log/media-pipeline/config-interface-out.log',
      log_file: '/var/log/media-pipeline/config-interface.log',
      time: true
    },
    {
      name: 'db-viewer',
      script: 'db_viewer.py',
      interpreter: 'python3',
      cwd: '/opt/media-pipeline',
      user: 'media-pipeline',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      env: {
        NODE_ENV: 'production',
        PORT: 8084
      },
      error_file: '/var/log/media-pipeline/db-viewer-error.log',
      out_file: '/var/log/media-pipeline/db-viewer-out.log',
      log_file: '/var/log/media-pipeline/db-viewer.log',
      time: true
    },
    {
      name: 'syncthing',
      script: 'syncthing',
      args: '-gui-address=0.0.0.0:8385',
      cwd: '/opt/media-pipeline',
      user: 'media-pipeline',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      error_file: '/var/log/media-pipeline/syncthing-error.log',
      out_file: '/var/log/media-pipeline/syncthing-out.log',
      log_file: '/var/log/media-pipeline/syncthing.log',
      time: true
    }
  ]
};
