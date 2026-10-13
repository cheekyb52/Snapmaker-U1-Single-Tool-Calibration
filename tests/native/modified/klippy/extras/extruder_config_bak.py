# Snapmaker U1 Single Tool Calibration
# Project version: 0.1.0 | Updated: 2026-10-12
# Project: https://github.com/cheekyb52/Snapmaker-U1-Single-Tool-Calibration
# Calibration-project modifications; GPL-3.0, see LICENSE and NOTICE.md.

import json
import math
import os
import tempfile
import logging, queuefile

EXTRUDER_CONFIG_FILE = "extruder_config.json"
EXTRUDER_BASE_POSITION_FILE = "extruder_base_position.json"
OFFSET_REFERENCE_KEY = "_offset_reference"

class ExtruderConfigBak:
    def __init__(self, config):
        self.config = config
        self.printer = config.get_printer()
        self.reactor = self.printer.get_reactor()
        self._offset_reference = None
        self.config_path = os.path.join(self.printer.get_snapmaker_config_dir("persistent"),
                                      EXTRUDER_CONFIG_FILE)
        self.old_config_path = os.path.join(self.printer.get_snapmaker_config_dir(),
                                          EXTRUDER_CONFIG_FILE)
        self.base_position_config_path = os.path.join(self.printer.get_snapmaker_config_dir(),
                                      EXTRUDER_BASE_POSITION_FILE)
        if self.config_path == self.old_config_path:
            raise config.error("Config path and old config path are identical: %s" % (self.config_path,))

        # Register GCode commands
        gcode = self.printer.lookup_object('gcode')
        gcode.register_command('DELETE_EXTRUDER_BACKUP_CONFIG',
                             self.cmd_DELETE_EXTRUDER_BACKUP_CONFIG,
                             desc="Delete extruder backup config file")

    def cmd_DELETE_EXTRUDER_BACKUP_CONFIG(self, gcmd):
        # Check if deletion is permitted by checking for permission file
        if not self.printer.check_extruder_config_permission():
            raise gcmd.error("Deletion of extruder backup config files is not allowed.")

        deleted_files = []
        error_messages = []

        # Files to delete
        files_to_delete = [
            self.config_path,
            # self.base_position_config_path,
            self.old_config_path
        ]

        # Delete config files
        for file_path in files_to_delete:
            if os.path.exists(file_path):
                try:
                    os.unlink(file_path)
                    deleted_files.append(file_path)
                except Exception as e:
                    error_messages.append(f"Failed to delete config file {file_path}: {str(e)}")

        # Respond with results
        if deleted_files:
            gcmd.respond_info("Extruder config files deleted successfully:")
            for file_path in deleted_files:
                logging.info(f"  - {file_path}")

        if error_messages:
            for error_msg in error_messages:
                gcmd.respond_info(error_msg)

        if not deleted_files and not error_messages:
            gcmd.respond_info("No extruder config files found to delete")

    def get_extruder_config(self, extruder_name, field_name=None):
        """Get extruder configuration from JSON file"""
        # Determine which config file to read based on field_name
        config_file = self.config_path
        if field_name == 'base_position':
            config_file = self.base_position_config_path

        if not os.path.exists(config_file):
            return None
        try:
            with open(config_file, 'r') as f:
                config_data = json.load(f)
            if extruder_name not in config_data:
                return None
            extruder_config = config_data[extruder_name]
            if field_name is None:
                return extruder_config
            value = extruder_config
            for key in field_name.split('.'):
                if isinstance(value, (list, tuple)) and key.isdigit():
                    key = int(key)
                    if key >= len(value):
                        return None
                    value = value[key]
                elif isinstance(value, dict):
                    if key not in value:
                        return None
                    value = value[key]
                else:
                    return None
            return value
        except json.JSONDecodeError:
            logging.error(f"Error: The configuration file {config_file} is not valid JSON")
            return None
        except IOError:
            logging.error(f"Error: Unable to read the configuration file {config_file}")
            return None
        except Exception as e:
            logging.error(f"Unknown error: {str(e)}")
            return None

    def _save_config_atomically(self, config_path, data):
        try:
            json_content = json.dumps(data, indent=4)
            queuefile.sync_write_file(self.reactor, config_path, json_content, flush=True, safe_write=True)
            logging.info("Extruder config saved successfully to %s. \nData: %s", config_path, data)

        except Exception as e:
            logging.error(f"Failed to save extruder config to {config_path}: {str(e)}")
            raise

    @staticmethod
    def validate_base_position(value):
        if (not isinstance(value, (list, tuple)) or len(value) != 3
                or any(type(v) not in (int, float) or not math.isfinite(v)
                       for v in value)):
            raise ValueError("Expected three finite base-position coordinates")
        return list(value)

    def _reference_from_data(self, data):
        # Legacy files have no reference metadata and retain dynamic centering.
        if not isinstance(data, dict):
            raise ValueError("Invalid base-position config structure")
        if OFFSET_REFERENCE_KEY not in data:
            return None
        metadata = data[OFFSET_REFERENCE_KEY]
        if (not isinstance(metadata, dict)
                or type(metadata.get('version')) is not int
                or metadata['version'] != 1):
            raise ValueError("Unsupported offset reference metadata")
        reference = self.validate_base_position(metadata['position'])
        anchor = self.validate_base_position(metadata['t0_base_position'])
        current_t0 = self.validate_base_position(data['extruder']['base_position'])
        if anchor != current_t0 or reference[2] != anchor[2]:
            raise ValueError("Offset reference does not match saved T0")
        return reference

    def load_offset_reference(self, config):
        self._offset_reference = None
        if not os.path.exists(self.base_position_config_path):
            return
        try:
            with open(self.base_position_config_path, 'r') as f:
                data = json.load(f)
            self._offset_reference = self._reference_from_data(data)
        except (OSError, ValueError, TypeError, KeyError) as e:
            # Do not silently recenter a machine with unreadable reference data.
            raise config.error("Unable to load offset reference: %s" % (e,))

    def get_offset_reference(self):
        if self._offset_reference is None:
            return None
        return list(self._offset_reference)

    def get_status(self, eventtime):
        # CFG callers must check this capability before using the new option;
        # older SET_EXTRUDER_BASE_POSITION handlers ignore unknown parameters.
        return {'preserve_reference_supported': True,
                'offset_reference': self.get_offset_reference()}

    def update_base_positions(self, updates, reference=None,
                              expected_positions=None):
        """Commit positions and reference in one stock atomic JSON write.

        reference=None retains legacy save semantics: discard a frozen frame
        and derive the midpoint from the new table. Independent saves pass the
        existing frame and an expected table to reject stale in-memory data.
        """
        try:
            with open(self.base_position_config_path, 'r') as f:
                data = json.load(f)
            if not isinstance(data, dict):
                raise ValueError("Invalid base-position config structure")
            if expected_positions is not None:
                if self._reference_from_data(data) != self._offset_reference:
                    raise ValueError("Saved offset reference changed")
                for name, expected in expected_positions.items():
                    expected = self.validate_base_position(expected)
                    if data[name]['base_position'] != expected:
                        raise ValueError("Saved calibration changed for %s" % name)
            for name, value in updates.items():
                value = self.validate_base_position(value)
                entry = data.setdefault(name, {})
                if not isinstance(entry, dict):
                    raise ValueError("Invalid extruder config for %s" % name)
                entry['base_position'] = value
            if reference is None:
                data.pop(OFFSET_REFERENCE_KEY, None)
            else:
                reference = self.validate_base_position(reference)
                for name in ('extruder', 'extruder1', 'extruder2', 'extruder3'):
                    self.validate_base_position(data[name]['base_position'])
                anchor = list(data['extruder']['base_position'])
                if reference[2] != anchor[2]:
                    raise ValueError("Independent reference must retain T0 Z")
                data[OFFSET_REFERENCE_KEY] = {
                    'version': 1, 'position': reference,
                    't0_base_position': anchor,
                }
            json.dumps(data, allow_nan=False)
            self._save_config_atomically(self.base_position_config_path, data)
        except (OSError, ValueError, TypeError, KeyError) as e:
            logging.error("Unable to save base positions: %s", e)
            return False
        except Exception as e:
            logging.exception("Atomic base-position save failed: %s", e)
            return False
        # Publish the frame only after persistence succeeds.
        self._offset_reference = None if reference is None else list(reference)
        return True

    def update_extruder_config(self, extruder_name, field_name=None, value=None):
        """Update extruder configuration in JSON file with atomic write"""
        if field_name == 'base_position':
            return self.update_base_positions({extruder_name: value})
        config_file = self.config_path
        if field_name == 'base_position':
            config_file = self.base_position_config_path

        if not os.path.exists(config_file):
            logging.error(f"Config file {config_file} does not exist")
            return False

        try:
            with open(config_file, 'r') as f:
                config_data = json.load(f)
                if not isinstance(config_data, dict):
                    raise ValueError("Invalid config structure")
        except (json.JSONDecodeError, ValueError, IOError) as e:
            logging.error(f"Error processing config file {config_file}: {str(e)}")
            return False

        try:
            if extruder_name not in config_data:
                config_data[extruder_name] = {}

            if field_name is None:
                if value is None:
                    logging.error("Both field_name and value cannot be None")
                    return False
                config_data[extruder_name] = value
            else:
                current = config_data[extruder_name]
                keys = field_name.split('.')
                last_key = keys[-1]
                for key in keys[:-1]:
                    if isinstance(current, (list, tuple)) and key.isdigit():
                        key = int(key)
                        if key >= len(current):
                            raise IndexError("Index out of range")
                        current = current[key]
                    elif isinstance(current, dict):
                        if key not in current:
                            current[key] = {}
                        current = current[key]
                    else:
                        raise TypeError("Invalid config structure")
                if isinstance(current, (list, tuple)) and last_key.isdigit():
                    last_key = int(last_key)
                    if last_key >= len(current):
                        raise IndexError("Index out of range")
                    current[last_key] = value
                elif isinstance(current, dict):
                    current[last_key] = value
                else:
                    raise TypeError("Invalid config structure")
            json.dumps(config_data)  # Validate JSON serialization
        except (IndexError, TypeError, ValueError) as e:
            logging.error(f"Invalid config update: {str(e)}")
            return False

        # Use atomic save method
        try:
            self._save_config_atomically(config_file, config_data)
            return True
        except Exception as e:
            logging.error(f"Error during atomic update: {str(e)}")
            return False

    def extruder_config_bak(self, config):
        """Backup all extruder configs to JSON file"""
        if os.path.exists(self.old_config_path) and not os.path.exists(self.config_path):
            self._migrate_existing_backup()

        if os.path.exists(self.config_path) and os.path.exists(self.base_position_config_path):
            return True

        try:
            extruder_park_data = {}
            extruder_base_position_data = {}
            for i in range(99):
                section = 'extruder'
                if i:
                    section = 'extruder%d' % (i,)
                if not config.has_section(section):
                    break
                extruder_config = config.getsection(section)
                _xy_park_position = _y_idle_position = _base_position = None

                xy_park_position = extruder_config.get("xy_park_position", None)
                if xy_park_position is not None:
                    xy_park_position = extruder_config.getlists(
                        'xy_park_position', seps=(',', '\n'), count=2, parser=float)
                    _xy_park_position = list(xy_park_position[0])
                    _y_idle_position = extruder_config.getfloat(
                        'y_idle_position', 50., minval=0.)

                if extruder_config.get('base_position', None) is not None:
                    base_position = extruder_config.getlists(
                        'base_position', seps=(',', '\n'), parser=float)
                    if base_position is not None and len(base_position[0]) == 3:
                        _base_position = [base_position[0][i] for i in range(0, 3)]

                if _xy_park_position is None or _y_idle_position is None:
                    raise config.error(
                        f"{section} _xy_park_position or _y_idle_position not configured")

                # Store data in separate dictionaries
                extruder_park_data[section] = {
                    'xy_park_position': _xy_park_position,
                    'y_idle_position': _y_idle_position
                }


                extruder_base_position_data[section] = {
                    'base_position': _base_position
                }

            # Save park data to new location (persistent directory)
            if extruder_park_data and not os.path.exists(self.config_path):
                self._save_config_atomically(self.config_path, extruder_park_data)

            # Save base position data to new file in old location (snapmaker directory)
            if extruder_base_position_data and not os.path.exists(self.base_position_config_path):
                self._save_config_atomically(self.base_position_config_path, extruder_base_position_data)

        except Exception as e:
            logging.error(f"Failed to prepare extruder config: {str(e)}")
            return False
        return True

    def _migrate_existing_backup(self):
        """Migrate existing backup from old format to new format"""
        try:
            # Load existing data from old config file
            with open(self.old_config_path, 'r') as f:
                old_config_data = json.load(f)

            extruder_park_data = {}
            extruder_base_position_data = {}

            # Separate park data from base position data
            for section_name, section_data in old_config_data.items():
                if section_name.startswith('extruder'):
                    # Extract park data
                    if 'xy_park_position' in section_data and 'y_idle_position' in section_data:
                        extruder_park_data[section_name] = {
                            'xy_park_position': section_data['xy_park_position'],
                            'y_idle_position': section_data['y_idle_position']
                        }

                    # Extract base position data
                    if 'base_position' in section_data and section_data['base_position'] is not None:
                        extruder_base_position_data[section_name] = {
                            'base_position': section_data['base_position']
                        }

            # Save separated data to appropriate locations
            if extruder_park_data:
                self._save_config_atomically(self.config_path, extruder_park_data)
            if extruder_base_position_data:
                self._save_config_atomically(self.base_position_config_path, extruder_base_position_data)

            # try:
            #     os.rename(self.old_config_path, self.old_config_path + ".tmp")
            #     logging.info("Successfully migrated existing backup to new format and renamed old file")
            # except Exception as e:
            #     logging.warning(f"Failed to rename old config file after migration: {e}")

            logging.info("Successfully migrated existing backup to new format")

        except Exception as e:
            logging.warning(f"Failed to migrate existing backup: {e}")
        return

def load_config(config):
    extruder_bak = ExtruderConfigBak(config)
    extruder_bak.extruder_config_bak(config)
    extruder_bak.load_offset_reference(config)
    return extruder_bak
