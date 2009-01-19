//
//  DatePickerViewController.m
//  TaskCoach
//
//  Created by Jérôme Laheurte on 19/01/09.
//  Copyright 2009 __MyCompanyName__. All rights reserved.
//

#import "DatePickerViewController.h"

@implementation DatePickerViewController

@synthesize picker;

- initWithDate:(NSString *)theDate target:(id)theTarget action:(SEL)theAction
{
	if (self = [super initWithNibName:@"DatePickerView" bundle:[NSBundle mainBundle]])
	{
		target = theTarget;
		action = theAction;

		if (theDate)
		{
			date = [NSDate dateWithNaturalLanguageString:theDate];
		}
		else
		{
			date = [NSDate date];
		}
	}

	return self;
}

- (void)dealloc
{
	[picker release];

	[super dealloc];
}

- (void)viewDidLoad
{
	picker.date = date;
}

- (IBAction)onConfirm:(UIButton *)button
{
	[target performSelector:action withObject:picker.date];
}

- (IBAction)onCancel:(UIButton *)button
{
	[target performSelector:action withObject:nil];
}

@end
