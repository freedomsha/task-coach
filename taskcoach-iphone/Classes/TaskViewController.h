//
//  TaskViewController.h
//  TaskCoach
//
//  Created by Jérôme Laheurte on 15/01/09.
//  Copyright 2009 Jérôme Laheurte. See COPYING for details.
//

#import <UIKit/UIKit.h>

#import "ODCalendarDayTimelineView.h"

#import "PositionStore.h"

@class CategoryViewController;
@class SearchCell;
@class TaskCell;
@class PaperHeaderView;

@interface TaskViewController : UIViewController <UIAlertViewDelegate, RestorableController, UISearchBarDelegate,
	ODCalendarDayTimelineViewDelegate, NSFetchedResultsControllerDelegate, UIActionSheetDelegate>
{
	BOOL shouldEdit;
	BOOL isCreatingTask;

	UITableViewController *tableViewController;
	CategoryViewController *categoryController;

	SearchCell *searchCell;
	TaskCell *currentCell;
	NSIndexPath *tapping;
	NSTimer *minuteTimer;

	ODCalendarDayTimelineView *calendarView;
	UISearchBar *calendarSearch;
	UIToolbar *toolbar;

	NSFetchedResultsController *results;
	NSIndexPath *selected;

	UIActionSheet *groupSheet;
	UIBarButtonItem *groupButton;
	UIPopoverController *popCtrl;

	PaperHeaderView *headerView;
	BOOL incrementalSearch;
}

@property (nonatomic, readonly) UITableView *tableView;
@property (nonatomic, retain) IBOutlet UITableViewController *tableViewController;
@property (nonatomic, retain) IBOutlet ODCalendarDayTimelineView *calendarView;
@property (nonatomic, retain) IBOutlet UISearchBar *calendarSearch;
@property (nonatomic, retain) IBOutlet UIToolbar *toolbar;
@property (nonatomic, assign) IBOutlet CategoryViewController *categoryController; // for iPad
@property (nonatomic, assign) IBOutlet UIBarButtonItem *groupButton;
@property (nonatomic, assign) UIPopoverController *popCtrl;

@property (nonatomic, retain) IBOutlet PaperHeaderView *headerView;

- (IBAction)onAddTask:(UIBarButtonItem *)button;
- (IBAction)onSync:(UIBarButtonItem *)button;
- (IBAction)onSwitch:(UIBarButtonItem *)button;
- (IBAction)onChangeGrouping:(UIBarButtonItem *)button;

- initWithCategoryController:(CategoryViewController *)controller edit:(BOOL)edit;

- (void)populate;
- (NSPredicate *)predicate;

- (void)childWasPopped;

@end
