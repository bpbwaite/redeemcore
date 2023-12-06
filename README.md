# RedemptionCore

RedemptionCore is in beta. There will be bugs and inefficiencies.

One (1) TVs have been destroyed by RedemptionCore. [Clip](https://www.twitch.tv/patrickw3d/clip/LongTransparentTardigradeKAPOW-0oH3BWzX0tLzxPOD)

## Use Case

The purpose RedemptionCore is to allow programming the GPIO pins on a Raspberry Pi to react to events during Twitch stream. For example, "turn on a light when you receive a donation or subscription". The scope has grown to include bits, follows, and even point redeems with custom messages.

## Installation & Dependencies

Barebones at the moment:

build with ```python -m build```

install with ```pip install .```

run with ```python -m RedemptionCore```

You also need StreamElements and pigpiod ```(sudo pigpiod)```

## The ```settings.ini``` file

Is the basic config used before any actions can be registered. At the least, you should specify:

+ A channel to watch (name as it appears in your URL)
+ The Twitch ID of a "bot" user - the default is StreamElements

### Administrators

You may also specify one or more administrators by ID. They will be able to run actions manually by chatting. See [running actions manually](#running-actions-manually) for a how-to.

### Developer/Advanced Settings

If you have a custom tip/sub message in StreamElements, you can edit the regular expressions that capture this information.

## The ```actions.json``` file

### What is an Action?

There are now 3 categories of actions:

+ 'List': These are events that can be run when someone donates to you in the form of a tip, bits, subscription, new follow, or points. They are defined by [action fields](#action-fields).
+ 'Initialization': Actions that run only once when the program starts.
+ 'Periodic': Actions run on their own repeatedly.

The ```actions.json``` file is a list of actions stored in a JSON object. Some things to note:

+ Order actions based on priority; highest at the top
+ Events shall run in the listed order
+ Give "exact" actions a higher priority than "inexact" actions - unless you want every inexact action to run when a large enough "exact" donation is made
+ Custom rewards for points are advanced, as they take a message from a viewer to control something.

### Action Fields

Every list action has certain required fields:

+ 'name': A friendly, unique name for this action. (string)
+ 'accepted_modes': The sources that can trigger this action. Types are 'tips', 'bits', 'subs', 'follows', and 'points'. See also the [multiple-credit](#Multiple Credits) option. (list of string)
+ 'cost': A number of cents, bits, or points required to run the action. Subscription and follow actions always run if they are one of the accepted modes. (integer or string)
+ 'exact': If false, the cost for this action is a minimum threshold rather than a strict requirement. Implicitly true for points-actions. (boolean)
+ 'steps': (list of objects)

Point-actions required fields:

+ 'uuid_pts': The UUID reported over IRC when points are redeemed. (string)
+ 'regexp_pts': A regular expression. The groups in the first match can be used as [macros](#macros) in the steps ran by the action. (string)

Note: Generally each action accepts just one mode. You may have copies of an action where the only difference is the accepted modes and cost. It is not recommended to mix point-actions with the other types.

### Multiple Credits

Add the 'multiple-credit' option to the 'accepted_modes' field of an inexact tips or bits action to run multiple times, based on the size of the donation. Multiple credit actions should not use certain macros.

### Initialization and Periodic Actions

These are automatic actions. Actions that run on startup are called initialization actions. Their action fields include 'name' and 'steps'. Periodic actions run repeatedly without any input. They are like initialization actions but also have a 'period' field, where you can enter an interval in milliseconds. Automatic actions should not use certain macros.

### Steps

Steps are a block of code that run on the Raspberry Pi; such as controlling GPIO.
See the default ```actions.json``` template

Supported functions:
**DELAY**, **SETPIN**, **TOGGLEPIN**, **SETPWM**, **SERVO**

### Macros

Can be used in steps

+ **HIGH** - evaluates to true, for turning on digital pins
+ **LOW** - evaluates to false, for turning off digital pins

+ **GIVEN** - evaluates to the amount donated, regardless of the cost. Always evalues to 500 upon subscriptions, and 0 for automatic or multiple-credit actions.
+ **REGEX_1, REGEX_2, ... REGEX_*n*** - evaluate to regular expression groups that the viewer supplied for a Points-action

### Running Actions Manually

Type in chat: ```force=<type><amount>``` to simlulate a donation. You must be an [administrator](#administrators). Valid examples:

+ ```force= $5.00``` - a $5 tip
+ ```force= T1000``` - a $10 tip (i.e., 1000 cents)
+ ```force= B700``` - 700 bits
+ ```force= S500``` - a subscription
+ ```force= P650 abc``` - 650 points with message 'abc'
+ ```force= F1``` - new follow

### Log File

WIP
