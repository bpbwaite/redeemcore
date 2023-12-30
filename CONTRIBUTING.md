# Contributing

## Notes

I did not expect the projects to be this copmlex, but continued support from my users has encouraged the addition of many extra features.

There are no unit tests because this software is procedural, not functional. In my opinion, There are too many side effects to be written functionally.

## Feature Plans

- [ ] crowd-fundable actions
- [ ] trigger action from a step of another action
- [ ] random values in range / step function subcommand
- [x] limited quantity redeems
- [x] trigger type 'raid'
- [x] repeat actions on a timer
- [x] repeat action upon recv more than double its cost

## Issues

In order of priority:

- [x] queue message handling in a separate thread to not block socket ping/pong
- [x] semaphore the above
- [ ] write an easy to use bash script that performs startup, checks for updates, installs, etc
- [ ] need semaphore on file accessed by both server and application
