from plugins.pm_filter import advantage_spell_chok

async def spell_check(message):
    spell = await advantage_spell_chok(message)
    return spell