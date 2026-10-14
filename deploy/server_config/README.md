# deploy/server_config/

Copies of config files that live only on the production server. **Nothing
installs these automatically.** The files on the server are the ones that
run. These copies exist so the server can be rebuilt if it's lost.

| File                  | Goes to on the server                                   |
| --------------------- | ------------------------------------------------------- |
| `gunicorn.service`    | `/etc/systemd/system/gunicorn.service`                  |
| `nginx/ifiplatform`   | `/etc/nginx/sites-available/`, linked into `sites-enabled/` |
| `fail2ban/jail.local` | `/etc/fail2ban/jail.local`                              |

- The server's IP address is replaced with `<server-ip>`. Put the real one
  back when installing.
- The lines marked `# managed by Certbot` in the Nginx file were added by
  Certbot. On a new server, install the file without them and let
  `certbot --nginx` add them.
- **When you change one of these files on the server, copy the change
  here**, or the copies stop being useful.
- Every deploy runs [check_server_config.sh](../check_server_config.sh),
  which compares these copies with the live files. If one differs, a
  yellow warning appears at the top of the deploy run's page in GitHub
  Actions, and the log shows the difference. It never changes anything.

How to rebuild the server step by step: see
[docs/operations/server_setup.md](../../docs/operations/server_setup.md).
