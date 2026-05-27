# Stalwart Configuration

## Active Configuration

The active configuration file is located at:
- `/etc/stalwart/config.json`

## Example Backend Configurations

Example configuration files for different storage backends can be found in:
- `/usr/share/doc/stalwart/`

Available backend examples:
- `stalwart.postgres.json` - PostgreSQL backend
- `stalwart.mysql.json` - MySQL/MariaDB backend
- `stalwart.sqlite.json` - SQLite backend (simple, single-node)
- `stalwart.rocksdb.json` - RocksDB backend (recommended for single-node)
- `stalwart.foundationdb.json` - FoundationDB backend (distributed deployments)

## Switching Backends

To switch to a different backend:

1. Copy the desired example configuration:
   ```bash
   sudo cp /usr/share/doc/stalwart/stalwart.<backend>.json /etc/stalwart/config.json
   ```

2. Edit the configuration file and update the connection details:
   ```bash
   sudo vi /etc/stalwart/config.json
   ```

3. Ensure proper ownership:
   ```bash
   sudo chown stalwart:stalwart /etc/stalwart/config.json
   sudo chmod 644 /etc/stalwart/config.json
   ```

4. Restart the service:
   ```bash
   sudo systemctl restart stalwart
   ```

## Documentation

For more information about storage backends, visit:
- https://stalw.art/docs/storage/backends/
