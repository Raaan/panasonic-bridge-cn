"""Credentials are entered locally in HA; never log input or cloud payloads."""
import hashlib

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector

from . import DOMAIN
from .client import Client
from .transport import CloudError


class PanasonicFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        return await self._credentials('user', user_input)

    async def async_step_reconfigure(self, user_input=None):
        return await self._credentials('reconfigure', user_input)

    async def _credentials(self, step_id, user_input):
        errors = {}
        detail = 'integration / response'
        entry = self._get_reconfigure_entry() if step_id == 'reconfigure' else None
        if user_input is not None:
            username = user_input['username'].strip()
            unique = hashlib.sha256(username.encode()).hexdigest()
            # The current entry must be excluded when reconfiguring its account.
            if any(existing.unique_id == unique and
                   (entry is None or existing.entry_id != entry.entry_id)
                   for existing in self.hass.config_entries.async_entries(DOMAIN)):
                return self.async_abort(reason='already_configured')
            try:
                client = await self.hass.async_add_executor_job(Client)
                devices = await self.hass.async_add_executor_job(client.login, username, user_input['password'])
                if devices:
                    self.hass.data.setdefault(DOMAIN, {})['pending_' + unique] = client
                    credentials = {'username': username, 'password': user_input['password']}
                    if entry is not None:
                        return self.async_update_reload_and_abort(
                            entry, unique_id=unique, data_updates=credentials,
                            reason='reconfigure_successful')
                    await self.async_set_unique_id(unique)
                    return self.async_create_entry(title='松下智家（本地验证）', data={
                        **credentials})
                errors['base'] = 'no_devices'
            except CloudError as error:
                detail = error.safe_detail
                errors['base'] = 'cannot_connect'
            except Exception:
                errors['base'] = 'cannot_connect'
        username_field = (vol.Required('username', default=entry.data['username'])
                          if entry is not None else vol.Required('username'))
        return self.async_show_form(step_id=step_id, errors=errors,
                                    description_placeholders={'detail': detail}, data_schema=vol.Schema({
            username_field: str,
            vol.Required('password'): selector.TextSelector(
                selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)),
        }))
