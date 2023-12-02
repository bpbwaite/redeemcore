# RedemptionCore

RedeemCore is in beta. There will be bugs and inefficiencies.

## Use Case

The purpose RedemptionCore is to allow programming the GPIO pins on a Raspberry Pi to react to events during Twitch stream. For example, "turn on a light when you receive a donation or subscription". The scope has grown to include Bits and even Point redeems with custom messages.

## Installation

Barebones at the moment:

build with ```python -m build```

install with ```pip install .```

run with ```python -m RedemptionCore```

## The ```settings.ini``` file

Is the basic config used before any Actions can be registered. At the least, you should specify:

+ A channel to watch (name as it appears in your URL)
+ The Twitch ID of a "bot" user - the default is StreamElements

### Administrators

You may also specify one or more administrators by ID. They will be able to run Actions manually by chatting. See ["Running Actions Manually"](#running-actions-manually) for a how-to.

### Developer/Advanced Settings

If you have a custom tip/sub message in StreamElements, you can edit the regular expressions that capture this information.

## The ```actions.json``` file

### What is an Action?

These are events that can be run when someone donates to you in the form of a tip, bits, subscription, or points. They are defined by [action fields](#action-fields).

The ```actions.json``` file is a list of Actions stored in a JSON object. Some things to note:

+ Order Actions based on priority; highest at the top
+ Events shall run in the listed order
+ Give "exact" Actions a higher priority thatn "inexact" Actions - unless you want every inexact Action to run when a large enough "exact" donation is made
+ Custom rewards for points are advanced, as they take a message from a viewer to control something.

### Action Fields

Every Action has certain required fields:

+ 'name': A friendly, unique name for this Action. (string)
+ 'accepted_modes': The sources that can trigger this action. Types are 'tips', 'bits', 'subs', and 'points'. (list of string)
+ 'cost': A number of cents, bits, or points required to run the Action. Subscription-actions always run if 'subs' is one of the accepted modes. (integer or string)
+ 'exact': If false, the cost for this Action is a minimum threshold rather than a strict requirement. Implicitly true for points-actions. (boolean)
+ 'steps': (list of objects)

Point-actions required fields:

+ 'uuid_pts': The UUID reported over IRC when points are redeemed. (string)
+ 'regexp_pts': A regular expression. The groups in the first match can be used as [macros](#macros) in the steps ran by the Action. (string)

Note: Generally each Action accepts just one mode. You may have copies of an Action where the only difference is the accepted modes and cost. It is not recommended to mix point-actions with the other types.

### Steps

Steps are a block of code that run on the Raspberry Pi; such as controlling GPIO.
See the default ```actions.json``` template

Supported functions:
**DELAY**, **SETPIN**, **TOGGLEPIN**, **SETPWM**, **SERVO**

### Macros

Can be used in steps

+ **HIGH** - evaluates to true, for turning on digital pins
+ **LOW** - evaluates to false, for turning off digital pins
+ **GIVEN** - evaluates to the amount donated, regardless of the cost. Always evalues to 500 upon subscriptions
+ **REGEX_1, REGEX_2, ... REGEX_*n*** - evaluate to regular expression groups that the viewer supplied for a Points-action.

### Running Actions Manually

Type in chat: ```force=<type><amount>``` to simlulate a donation. You must be an [administrator](#administrators). Valid examples:

+ ```force= $5.00``` - a $5 tip
+ ```force= T1000``` - a $10 tip (i.e., 1000 cents)
+ ```force= B700``` - 700 bits
+ ```force= S500``` - a subscription
+ ```force= P650 abc``` - 650 points with message 'abc'
