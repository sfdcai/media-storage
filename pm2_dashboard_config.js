module.exports = {
  apps: [
    {
      name: 'pm2-dashboard',
      script: 'pm2',
      args: 'serve /opt/media-pipeline 9615 --name pm2-dashboard --spa',
      cwd: '/opt/media-pipeline',
      user: 'root',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      env: {
        NODE_ENV: 'production'
      },
      error_file: '/var/log/media-pipeline/pm2-dashboard-error.log',
      out_file: '/var/log/media-pipeline/pm2-dashboard-out.log',
      log_file: '/var/log/media-pipeline/pm2-dashboard.log',
      time: true
    }
  ]
};
