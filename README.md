# form-health-check

A daily check that your landing pages still load, still have their lead forms and still carry their tracking tags. When something breaks it posts to Slack. When everything passes it stays quiet.

I run a check like this on every page with live ad spend behind it. A form that stops submitting on a Friday evening costs the whole weekend's budget, and nobody finds out until Monday's report. This finds out at 7 AM.

## What it checks, per page

- HTTP status is 200.
- Load time under a limit you set.
- A `<form>` element exists.
- Any strings you expect inside the form markup (an id, a field name).
- Any tracking tag strings you expect on the page (a GTM container prefix, a GA4 measurement id).

## Install

```
pip install -r requirements.txt
cp config.example.json config.json
```

Edit `config.json` with your pages, hints and (optionally) a Slack incoming webhook.

## Use

```
python form_health_check.py --config config.json
python form_health_check.py --config config.json --quiet
```

Example cron entry, every day at 07:00:

```
0 7 * * * cd /opt/form-health-check && /usr/bin/python3 form_health_check.py --config config.json --quiet
```

## Limits

- This checks that the form markup and tags are present, not that a submission reaches your CRM. For that, submit a test lead weekly and confirm it lands with its source fields (see the attribution audit playbook).
- Pages that render the form only with JavaScript will need a browser-based check instead.

## Related

The [paid media pre-launch QA checklist](https://github.com/ammar-alkazaz/marketing-automation-playbooks/blob/main/04-paid-media-pre-launch-qa-checklist.md) and the [attribution and tracking audit](https://github.com/ammar-alkazaz/marketing-automation-playbooks/blob/main/05-attribution-and-tracking-audit.md) describe where this fits.

MIT License.
